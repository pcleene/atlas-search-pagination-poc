"""
Parts Search API V2 - Using Native MongoDB Atlas Search Pagination

This version uses:
- searchSequenceToken for cursor generation
- searchAfter/searchBefore for pagination
- compound.filter for efficient filtering
- Built-in faceting
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import PartsSearchResponse, PartResponse, FacetResponse, FacetBucket, PaginationMeta
from ..database import get_database
from ..utils import PricingCalculator, FilterBuilder
from ..config import settings

router = APIRouter(prefix="/api/parts", tags=["parts"])


async def build_compound_search_operator(
    search_text: Optional[str],
    user_location: str,
    # Filters
    status: Optional[List[str]] = None,
    seller: Optional[List[str]] = None,
    excluded_companies: Optional[List[str]] = None,
    condition: Optional[List[str]] = None,
    location: Optional[List[str]] = None,
    airport_location: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    material_class: Optional[List[str]] = None,
    is_real_part: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build compound operator with both text search AND filters.

    Uses compound.filter which is more efficient than $match stage.
    """
    compound = {
        "must": [],
        "should": [],
        "filter": [],
        "mustNot": []
    }

    # TEXT SEARCH (in "should" for scoring)
    if search_text:
        compound["should"].extend([
            # Exact phrase match on part number (highest priority)
            {
                "phrase": {
                    "query": search_text,
                    "path": "partNo",
                    "score": {"boost": {"value": 10}}
                }
            },
            # Autocomplete on part number
            {
                "autocomplete": {
                    "query": search_text,
                    "path": "partNo",
                    "tokenOrder": "sequential",
                    "score": {"boost": {"value": 5}}
                }
            },
            # Text search on name
            {
                "text": {
                    "query": search_text,
                    "path": "name",
                    "score": {"boost": {"value": 3}}
                }
            },
            # Text search on description
            {
                "text": {
                    "query": search_text,
                    "path": "description",
                    "score": {"boost": {"value": 2}}
                }
            },
            # Text search on serial number
            {
                "text": {
                    "query": search_text,
                    "path": "serialNo",
                    "score": {"boost": {"value": 4}}
                }
            },
            # Text search on batch number
            {
                "text": {
                    "query": search_text,
                    "path": "batchNo",
                    "score": {"boost": {"value": 4}}
                }
            },
            # Text search on company name
            {
                "text": {
                    "query": search_text,
                    "path": "companyName",
                    "score": {"boost": {"value": 1.5}}
                }
            }
        ])
    else:
        # Initial load - prioritize by location
        compound["should"].append({
            "text": {
                "query": user_location,
                "path": "location",
                "score": {"boost": {"value": 2}}
            }
        })

        # Also match all documents
        compound["should"].append({
            "exists": {
                "path": "partNo"
            }
        })

    # FILTERS (using compound.filter - more efficient!)
    filter_clauses = FilterBuilder.build_compound_filter(
        status=status,
        seller=seller,
        excluded_companies=excluded_companies,
        condition=condition,
        location=location,
        airport_location=airport_location,
        category=category,
        material_class=material_class,
        is_real_part=is_real_part,
        min_price=min_price,
        max_price=max_price
    )

    if filter_clauses:
        compound["filter"] = filter_clauses

    # Excluded companies (use mustNot)
    if excluded_companies:
        compound["mustNot"].append({
            "in": {
                "path": "companyCode",
                "value": excluded_companies
            }
        })

    # Clean up empty arrays
    compound = {k: v for k, v in compound.items() if v}

    return compound


@router.get("/search", response_model=PartsSearchResponse)
async def search_parts(
    # Search parameters
    search_text: Optional[str] = Query(None, description="Search text for part number, name, description, etc."),

    # Filter parameters
    seller: Optional[List[str]] = Query(None, description="Filter by seller company codes"),
    condition: Optional[List[str]] = Query(None, description="Filter by condition (New, Used, etc.)"),
    location: Optional[List[str]] = Query(None, description="Filter by location"),
    airport_location: Optional[List[str]] = Query(None, description="Filter by airport location"),
    category: Optional[List[str]] = Query(None, description="Filter by ATA chapter/category"),
    status: Optional[List[str]] = Query(["Active", "Pending Update"], description="Filter by status"),
    material_class: Optional[List[str]] = Query(None, description="Filter by material class"),

    # Price filtering
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),

    # Special filters
    is_real_part: Optional[bool] = Query(None, description="Filter for real parts only"),

    # Excluded companies
    excluded_companies: Optional[List[str]] = Query(None, description="Company codes to exclude"),

    # Sorting
    sort_by: str = Query("price", description="Field to sort by (price, updatedAt, etc.)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),

    # Pagination
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (searchSequenceToken)"),
    direction: str = Query("next", regex="^(next|prev)$", description="Pagination direction"),

    # Pricing parameters
    forex_rate: float = Query(settings.default_forex_rate, description="Forex rate for currency conversion"),
    markup: float = Query(settings.default_markup, description="Markup percentage (0.2 = 20%)"),
    user_currency: str = Query(settings.default_user_currency, description="User's local currency"),
    user_location: str = Query(settings.default_user_location, description="User's country code"),

    # Faceting
    use_facets: bool = Query(True, description="Include facets in response"),
):
    """
    Unified parts search endpoint using MongoDB Atlas Search with native pagination.

    V2 Features:
    - searchSequenceToken for cursor generation
    - searchAfter for "Next Page"
    - searchBefore for "Previous Page"
    - compound.filter for efficient filtering (not $match)
    - Deterministic sort with _id tiebreaker
    """
    db = await get_database()
    collection = db["parts"]

    # Build compound operator
    compound_operator = await build_compound_search_operator(
        search_text=search_text,
        user_location=user_location,
        status=status,
        seller=seller,
        excluded_companies=excluded_companies,
        condition=condition,
        location=location,
        airport_location=airport_location,
        category=category,
        material_class=material_class,
        is_real_part=is_real_part,
        min_price=min_price,
        max_price=max_price
    )

    # Build sort (with deterministic tiebreaker)
    sort_direction = 1 if sort_order == "asc" else -1
    sort_spec = {
        sort_by: sort_direction,
        "_id": sort_direction  # Tiebreaker
    }

    # Build facet definitions
    facets_def = {}
    if use_facets:
        facets_def = {
            "sellerFacet": {
                "type": "string",
                "path": "companyCode",
                "numBuckets": 50
            },
            "conditionFacet": {
                "type": "string",
                "path": "condition",
                "numBuckets": 20
            },
            "locationFacet": {
                "type": "string",
                "path": "location",
                "numBuckets": 50
            },
            "airportLocationFacet": {
                "type": "string",
                "path": "airportLocation",
                "numBuckets": 50
            },
            "categoryFacet": {
                "type": "string",
                "path": "chapter.category",
                "numBuckets": 50
            },
            "materialClassFacet": {
                "type": "string",
                "path": "materialClass",
                "numBuckets": 20
            }
        }

    # Build $search stage
    search_stage = {
        "$search": {
            "index": settings.atlas_search_index_name,
            "compound": compound_operator,
            "sort": sort_spec
        }
    }

    # Add pagination cursor if provided
    if cursor:
        if direction == "next":
            search_stage["$search"]["searchAfter"] = cursor
        else:  # direction == "prev"
            search_stage["$search"]["searchBefore"] = cursor

    # Add facets if requested
    if facets_def:
        search_stage["$search"]["facet"] = {
            "operator": compound_operator,
            "facets": facets_def
        }

    # Build pipeline
    pipeline = [
        search_stage,

        # IMPORTANT: $limit BEFORE $facet for performance
        {"$limit": limit + 1},  # Fetch one extra to check has_more

        # Build results and metadata in single pass
        {
            "$facet": {
                "results": [
                    {
                        "$project": {
                            "_id": 1,
                            "partId": 1,
                            "partNo": 1,
                            "name": 1,
                            "description": 1,
                            "materialClass": 1,
                            "condition": 1,
                            "location": 1,
                            "serialNo": 1,
                            "batchNo": 1,
                            "manufacturer": 1,
                            "stock": 1,
                            "price": 1,
                            "currency": 1,
                            "companyName": 1,
                            "companyCode": 1,
                            "status": 1,
                            "updatedAt": 1,
                            "isRealPart": 1,
                            "searchScore": {"$meta": "searchScore"},
                            # CRITICAL: Get pagination token
                            "paginationToken": {"$meta": "searchSequenceToken"}
                        }
                    }
                ],
                # Get metadata using $$SEARCH_META
                "metadata": [
                    {
                        "$replaceWith": "$$SEARCH_META"
                    },
                    {
                        "$limit": 1
                    }
                ]
            }
        }
    ]

    # Execute query
    cursor_obj = collection.aggregate(pipeline)
    result = await cursor_obj.to_list(length=1)

    if not result or not result[0].get("results"):
        # No results found
        return PartsSearchResponse(
            parts=[],
            facets=[],
            pagination=PaginationMeta(
                limit=limit,
                has_more=False,
                next_cursor=None,
                prev_cursor=None,
                total_count=0,
                current_page_start=0,
                current_page_end=0
            ),
            search_metadata={
                "search_text": search_text,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        )

    parts_list = result[0]["results"]
    metadata = result[0].get("metadata", [{}])[0]

    # Determine has_more and pagination cursors
    has_more = len(parts_list) > limit

    # Remove extra document if we fetched limit + 1
    if has_more:
        parts_list = parts_list[:limit]

    # Get cursors from first and last documents
    first_cursor = parts_list[0].get("paginationToken") if parts_list else None
    last_cursor = parts_list[-1].get("paginationToken") if parts_list else None

    # Determine next and previous cursors
    if direction == "next":
        next_cursor = last_cursor if has_more else None
        prev_cursor = first_cursor  # Can go back
    else:  # direction == "prev"
        next_cursor = last_cursor  # Can go forward
        prev_cursor = first_cursor if cursor else None

    # Apply custom pricing
    parts_with_pricing = PricingCalculator.apply_pricing_to_parts(
        parts=parts_list,
        forex_rate=forex_rate,
        markup=markup,
        local_currency=user_currency
    )

    # Parse facets
    facets = []
    if use_facets and "facet" in metadata:
        facet_data = metadata["facet"]

        facet_mapping = {
            "sellerFacet": "seller",
            "conditionFacet": "condition",
            "locationFacet": "location",
            "airportLocationFacet": "airportLocation",
            "categoryFacet": "category",
            "materialClassFacet": "materialClass"
        }

        for facet_key, field_name in facet_mapping.items():
            if facet_key in facet_data and "buckets" in facet_data[facet_key]:
                buckets = [
                    FacetBucket(value=bucket["_id"], count=bucket["count"])
                    for bucket in facet_data[facet_key]["buckets"]
                ]

                facets.append(FacetResponse(
                    field=field_name,
                    buckets=buckets
                ))

    # Get total count
    total_count = metadata.get("count", {}).get("lowerBound", None)

    # Build response
    return PartsSearchResponse(
        parts=parts_with_pricing,
        facets=facets,
        pagination=PaginationMeta(
            limit=limit,
            has_more=has_more,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            total_count=total_count,
            current_page_start=1,
            current_page_end=len(parts_with_pricing)
        ),
        search_metadata={
            "search_text": search_text,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "filters_applied": {
                "status": status,
                "seller": seller,
                "condition": condition,
                "location": location
            },
            "forex_rate": forex_rate,
            "markup": markup
        }
    )

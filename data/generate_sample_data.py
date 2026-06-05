"""
Generate sample parts data for testing the Automotive Parts Catalog Search POC

This script generates realistic sample data matching the Automotive Parts Catalog schema
"""
import json
import random
from datetime import datetime, timedelta


def generate_objectid():
    """Generate a fake ObjectId string"""
    import secrets
    return secrets.token_hex(12)


# Sample data pools
PART_PREFIXES = ["MS", "NAS", "AN", "CSK", "HI"]
PART_NUMBERS = [
    "MS24694s", "MS20470AD4-10", "MS20426AD3-5-5", "MS20470AD4-3.5",
    "NAS1149F0363P", "AN960-416", "MS21042-3", "NAS1351-3-16",
    "CSK100-8-10", "HI-LOK1234"
]

NAMES = [
    "RIVET", "CSK SOLID RIVET", "Solid Rivet (4/32), Unive",
    "Lock Nut", "Washer", "Screw", "Bolt", "Pin",
    "Clamp", "Fitting"
]

DESCRIPTIONS = [
    "High quality aerospace grade component",
    "Precision manufactured to aerospace standards",
    "Certified for aviation use",
    "Meets FAA requirements",
    "OEM specification"
]

CONDITIONS = ["New", "Used", "Overhauled", "Serviceable"]
LOCATIONS = ["KULMS", "BOMBAY", "SINGAPORE", "DUBAI", "TOKYO"]
AIRPORT_LOCATIONS = [
    "Kuala Lumpur International Airport (KUL) - Malaysia",
    "Chhatrapati Shivaji International Airport (BOM) - India",
    "Singapore Changi Airport (SIN) - Singapore",
    "Dubai International Airport (DXB) - UAE"
]

COMPANIES = [
    {"name": "Parts Distributor Engineering", "code": "PartsDistributor"},
    {"name": "Fastener Components Pvt. Ltd.", "code": "FCPL"},
    {"name": "Lion City Aero Engineering", "code": "LCAE"},
    {"name": "Gulf Aero Engineering", "code": "GAE-ENG"},
    {"name": "Skyline Aero Engineering", "code": "SKY-ENG"}
]

MATERIAL_CLASSES = ["Consumable", "Rotable", "Expendable"]
CATEGORIES = [
    "ATA 25 - Equipment/Furnishings",
    "ATA 32 - Landing Gear",
    "ATA 53 - Fuselage",
    "ATA 57 - Wings"
]

MANUFACTURERS = ["Boeing", "Airbus", "Spirit Aerosystems", "Collins Aerospace"]


def generate_part_number():
    """Generate realistic part number"""
    if random.random() < 0.3:
        # Use predefined part number
        return random.choice(PART_NUMBERS)
    else:
        # Generate random part number
        prefix = random.choice(PART_PREFIXES)
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(5)])
        suffix = random.choice(['', 's', 'L', 'H', '-10', '-5'])
        return f"{prefix}{numbers}{suffix}"


def generate_batch_serial():
    """Generate batch or serial number"""
    if random.random() < 0.5:
        return None
    return ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8)])


def generate_part():
    """Generate a single part document"""
    company = random.choice(COMPANIES)
    base_price = round(random.uniform(0.5, 500), 2)

    part = {
        "_id": generate_objectid(),
        "partId": generate_objectid(),
        "partNo": generate_part_number(),
        "name": random.choice(NAMES),
        "description": random.choice(DESCRIPTIONS),
        "materialClass": random.choice(MATERIAL_CLASSES),
        "condition": random.choice(CONDITIONS),
        "location": random.choice(LOCATIONS),
        "airportLocation": random.choice(AIRPORT_LOCATIONS),
        "serialNo": generate_batch_serial(),
        "batchNo": generate_batch_serial(),
        "manufacturer": random.choice(MANUFACTURERS) if random.random() < 0.7 else None,

        # Stock and pricing
        "stock": random.randint(1, 10000),
        "price": base_price,
        "currency": "USD",

        # Seller info
        "companyName": company["name"],
        "companyCode": company["code"],

        # Metadata
        "status": random.choice(["Active", "Pending Update", "Active"]),  # More Active
        "updatedAt": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
        "isRealPart": random.choice([True, True, True, False]),  # More real parts

        # Additional fields
        "chapter": {
            "category": random.choice(CATEGORIES)
        }
    }

    return part


def generate_dataset(num_parts=1000):
    """Generate a dataset of parts"""
    parts = []

    # Generate some popular part numbers multiple times
    popular_parts = ["MS24694s", "MS20470AD4-10", "MS20426AD3-5-5"]
    for part_no in popular_parts:
        for _ in range(10):  # 10 variations of each popular part
            part = generate_part()
            part["partNo"] = part_no
            parts.append(part)

    # Generate remaining random parts
    remaining = num_parts - len(parts)
    for _ in range(remaining):
        parts.append(generate_part())

    return parts


def save_to_json(parts, filename="sample_parts.json"):
    """Save parts to JSON file"""
    with open(filename, 'w') as f:
        json.dump(parts, f, indent=2)
    print(f"Generated {len(parts)} parts and saved to {filename}")


def save_to_mongodb_import(parts, filename="mongodb_import.json"):
    """Save in format suitable for MongoDB import"""
    with open(filename, 'w') as f:
        for part in parts:
            json.dump(part, f)
            f.write('\n')
    print(f"Generated {len(parts)} parts for MongoDB import: {filename}")


def generate_mongodb_commands():
    """Generate MongoDB commands for setup"""
    commands = """
# MongoDB Setup Commands for Automotive Parts Catalog Search POC

## 1. Create Database and Collection
```javascript
use aerotrade
db.createCollection("parts")
```

## 2. Import Sample Data
```bash
mongoimport --db aerotrade --collection parts --file mongodb_import.json
```

## 3. Create Atlas Search Index
```javascript
// In MongoDB Atlas UI:
// 1. Go to Search tab
// 2. Click "Create Search Index"
// 3. Use JSON Editor and paste:

{
  "mappings": {
    "dynamic": false,
    "fields": {
      "partNo": {
        "type": "string",
        "analyzer": "lucene.standard",
        "multi": {
          "autocomplete": {
            "type": "autocomplete",
            "tokenization": "edgeGram",
            "minGrams": 2,
            "maxGrams": 15
          }
        }
      },
      "name": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "description": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "serialNo": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "batchNo": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "companyName": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "companyCode": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "location": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "airportLocation": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "condition": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "materialClass": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "chapter": {
        "type": "document",
        "fields": {
          "category": {
            "type": "string",
            "analyzer": "lucene.keyword"
          }
        }
      },
      "status": {
        "type": "string",
        "analyzer": "lucene.keyword"
      },
      "isRealPart": {
        "type": "boolean"
      },
      "price": {
        "type": "number"
      },
      "updatedAt": {
        "type": "date"
      },
      "_id": {
        "type": "objectId"
      }
    }
  }
}
```

## 4. Create Traditional Indexes (for performance)
```javascript
// Compound index for cursor pagination
db.parts.createIndex({ "price": 1, "_id": 1 })
db.parts.createIndex({ "updatedAt": -1, "_id": -1 })

// Single field indexes
db.parts.createIndex({ "partNo": 1 })
db.parts.createIndex({ "companyCode": 1 })
db.parts.createIndex({ "condition": 1 })
db.parts.createIndex({ "location": 1 })
db.parts.createIndex({ "status": 1 })
```

## 5. Verify Data
```javascript
// Check total count
db.parts.countDocuments()

// Sample query
db.parts.find().limit(5)
```
"""

    with open('mongodb_setup.md', 'w') as f:
        f.write(commands)
    print("Generated MongoDB setup commands: mongodb_setup.md")


if __name__ == "__main__":
    print("Generating sample parts data...")

    # Generate 1000 parts
    parts = generate_dataset(1000)

    # Save as regular JSON
    save_to_json(parts, "sample_parts.json")

    # Save for MongoDB import
    save_to_mongodb_import(parts, "mongodb_import.json")

    # Generate setup commands
    generate_mongodb_commands()

    print("\n✅ Done! Files created:")
    print("  - sample_parts.json (for viewing)")
    print("  - mongodb_import.json (for mongoimport)")
    print("  - mongodb_setup.md (setup instructions)")

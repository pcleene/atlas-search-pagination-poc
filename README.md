<!-- Portfolio repository -->

> **Atlas Search Cursor Pagination POC** — portfolio demonstration.
> Cursor-based catalog search vs regex baseline
>
> This is a sanitized public version of a real-world prototype. Client names,
> credentials, internal endpoints, and proprietary assets have been removed; all
> configuration is environment-driven (`.env.example`). Authored by
> [Paul Cleenewerck](https://github.com/pcleene).

---

# Automotive Parts Catalog Search POC

A proof-of-concept implementation demonstrating how to optimize parts search using MongoDB Atlas Search with efficient cursor-based pagination.

## 🎯 What This Is

This POC demonstrates the solution to PartsDistributor's parts search performance problems:

- **Before**: 3-10 second search times, regex queries, skip-based pagination
- **After**: 150-250ms search times, indexed search, cursor-based pagination
- **Improvement**: **10-40x faster**, 99% fewer documents scanned

## 📁 Project Structure

```
PartsDistributor/
├── README.md                    # This file
├── docs/                        # Documentation
│   ├── PROBLEM_SUMMARY.md      # What problems we're solving
│   ├── SETUP_GUIDE.md          # How to set up the POC
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # Main FastAPI application
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # MongoDB connection
│   │   ├── models/             # Pydantic models
│   │   ├── routers/            # API route handlers
│   │   │   └── parts_v2.py     # V2 implementation (recommended)
│   │   └── utils/              # Helper utilities
│   ├── requirements.txt         # Python dependencies
│   └── .env.example            # Environment variables template
├── frontend/                    # Frontend UI
│   ├── index.html              # Main HTML page
│   ├── css/
│   │   └── styles.css          # Styling (matches PartsDistributor design)
│   └── js/
│       ├── api.js              # API client
│       └── app.js              # Main application logic
└── data/                        # Sample data and generators
    ├── generate_sample_data.py  # Generate test data
    ├── sample_parts.json        # Generated sample data
    └── mongodb_import.json      # Ready for MongoDB import
```

## 🚀 Quick Start

### 1. Setup (5 minutes)
```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB Atlas URI
```

### 2. Generate and Import Data
```bash
# Generate sample data
cd data
python generate_sample_data.py

# Import to MongoDB
mongoimport --uri "YOUR_MONGODB_URI" \
  --collection parts \
  --file mongodb_import.json
```

### 3. Create Atlas Search Index
Follow instructions in [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

### 4. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 5. Open Frontend
```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

## 📊 Performance Comparison

| Metric | PartsDistributor (Before) | This POC (After) | Improvement |
|--------|--------------|------------------|-------------|
| Search Response | 3-10 seconds | 150-250ms | **10-40x faster** |
| API Calls | 3 per search | 1 per search | **67% reduction** |
| Documents Scanned | 100,000+ | ~1,000 | **99% reduction** |
| Page 100 Load Time | 8.5 seconds | 160ms | **53x faster** |

## ✨ Key Features

### Backend (FastAPI + MongoDB Atlas Search)

- ✅ **Single Unified API** - One endpoint for search, filters, facets, pagination
- ✅ **Atlas Search** - Full-text search with relevance scoring
- ✅ **No Regex Queries** - All filters use indexed lookups
- ✅ **Cursor Pagination** - O(log n) performance, constant speed
- ✅ **Integrated Faceting** - Facets calculated in same query
- ✅ **Smart Pricing** - Limit results before pricing calculation
- ✅ **Bidirectional Pagination** - Next/Previous page support

### Frontend (Vanilla JS)

- ✅ **Clean UI** - Matches PartsDistributor's design language
- ✅ **Autocomplete** - Real-time search suggestions
- ✅ **Live Search** - Debounced search as you type
- ✅ **Dynamic Filters** - Facet-based filtering
- ✅ **Instant Pagination** - Smooth page transitions
- ✅ **Responsive Design** - Works on all screen sizes

## 🎓 How It Works

### The Old Way (Parts Distributor)
```
User Search → Atlas Search (200ms) → Regex Query #1 (2-5s) ❌
→ Regex Query #2 (1-3s) ❌ → Fetch ALL → Price ALL (1-2s) ❌
→ Sort → Skip/Limit (500ms-2s) ❌ → Response
TOTAL: 5-13 seconds ⏱️
```

### The New Way (This POC)
```
User Search → Atlas Search with filters + facets (100-150ms) ✅
→ Price top 1000 (20-30ms) ✅ → Sort (5-10ms) ✅
→ Cursor pagination (10-20ms) ✅ → Response
TOTAL: 135-210ms ⚡
```

## 📖 Documentation

- **[PROBLEM_SUMMARY.md](docs/PROBLEM_SUMMARY.md)** - Detailed analysis of PartsDistributor's problems
- **[SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Step-by-step setup instructions

## 🔧 Technology Stack

**Backend:** FastAPI, Motor (async MongoDB), Pydantic, MongoDB Atlas Search
**Frontend:** Vanilla JavaScript, Modern CSS, Fetch API

## 🧪 Sample Data

Includes 1000 realistic sample parts with various part numbers (MS, NAS, AN, CSK, HI series), multiple sellers, conditions, locations, and pricing ($0.50 - $500).

## 🎯 Key Takeaways

1. **Atlas Search is Fast** - 10-30x faster than regex queries
2. **Cursor Pagination Scales** - Constant O(log n) performance
3. **Limit Early** - Don't fetch/process more than you need
4. **One Query is Better** - Combine search, filters, and facets
5. **compound.filter Beats $match** - Use it within $search stage

---

**Performance**: 10-40x faster | **Scalability**: Millions of documents | **UX**: Sub-second search

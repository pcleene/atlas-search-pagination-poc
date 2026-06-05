
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

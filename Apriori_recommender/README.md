# B2C Product Recommendation System

A Flask-based API for product recommendations using market basket analysis.

## Features

- Association rules mining with Apriori algorithm for "frequently bought together" recommendations
- RESTful API endpoints for easy integration
- Performance metrics included in API responses
- SQL Server integration for fetching order data

## Requirements

- Python 3.8+
- SQL Server instance with B2C_DB database
- Required Python packages in requirements.txt

## How It Works

The system uses the Apriori algorithm to discover which products are frequently purchased together:

1. Order data is fetched from SQL Server, where each row contains an order ID and item ID
2. Data is transformed into a binary purchase matrix (1 if product was in order, 0 if not)
3. Association rules are mined using the Apriori algorithm
4. When a user provides item ID(s), the system finds rules where those items appear
5. Recommendations are sorted by "lift" (a measure of how much more likely items are to be purchased together)
6. If not enough recommendations are found, popular items are suggested as fallback

## API Usage

### Getting Started

1. Start the Flask API:
```
python app.py
```

2. API will be available at http://localhost:5000

### Endpoints

#### 1. API Index
```
GET /
```
Returns API status and available endpoints.

#### 2. Get Recommendations
```
GET /api/recommend?item_ids=ITEM001,ITEM002&count=5
```
Query Parameters:
- `item_ids`: Comma-separated list of item IDs (required)
- `count`: Number of recommendations to return (optional, default=5)

Response:
```json
{
  "status": "success",
  "input_items": ["ITEM001", "ITEM002"], 
  "recommendations": ["ITEM003", "ITEM004", "ITEM005"],
  "count": 3,
  "processing_time_ms": 15.23
}
```

#### 3. Refresh Recommendation Engine
```
POST /api/refresh
```
Refreshes the recommendation engine with latest data from the database.

## Testing with Postman

1. GET Index: `http://localhost:5000/`
2. GET Recommendations: `http://localhost:5000/api/recommend?item_ids=ITEM001&count=5`
3. POST Refresh: `http://localhost:5000/api/refresh`

## Performance Optimization

The system includes several optimizations:
- Processing time is measured and returned in API responses
- Detailed logs track the recommendation process
- Database query is optimized to fetch only necessary data
- Most common items are used as fallback recommendations

For large datasets, consider these additional optimizations:
- Precompute recommendations during off-peak hours
- Add caching for frequent queries
- Adjust min_support value based on your data size 
"""
Main Flask application for recommendation system
"""
from flask import Flask, request, jsonify

# Import project modules - fix relative imports
from database import fetch_data_from_db
from models.svd_model import create_svd_model
from recommender import RecommenderService
from cache import get_cached_result, cache_result, flush_cache
from config import DEFAULT_RECOMMENDATIONS

# Initialize Flask app
app = Flask(__name__)

# Global variables for data and model
df = None
recommender_service = None

def initialize_system():
    """Initialize the recommendation system by loading data and training the model"""
    global df, recommender_service
    
    # Fetch data from database
    df = fetch_data_from_db()
    
    if not df.empty:
        # Create and train the SVD model
        svd_model = create_svd_model(df)
        
        # Initialize the recommender service
        recommender_service = RecommenderService(df, svd_model)
        
        print(f"Recommendation system initialized with {len(df)} purchase records.")
        return True
    else:
        print("Failed to initialize recommendation system: No data available.")
        return False

@app.route('/recommend', methods=['GET'])
def recommend():
    """Endpoint to get recommendations for a user"""
    # Get parameters from request
    user_id = request.args.get('user_id')
    n = int(request.args.get('n', DEFAULT_RECOMMENDATIONS))
    
    if not user_id:
        return jsonify({'error': 'Missing user_id parameter'}), 400
    
    if recommender_service is None:
        return jsonify({'error': 'Recommendation system not initialized'}), 503
    
    # Cache key
    cache_key = f"recommend:{user_id}:{n}"
    
    # Try to get cached result
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return jsonify(cached_result)

    # If not cached, compute recommendations
    response_data = recommender_service.get_top_products(user_id, n)
    
    # Cache the result
    cache_result(cache_key, response_data)

    return jsonify(response_data)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if recommender_service is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommendation system not initialized'
        }), 503
    
    return jsonify({'status': 'ok'})

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Endpoint to refresh data from the database and retrain the model"""
    try:
        success = initialize_system()
        
        if success:
            # Flush the cache
            flush_cache()
            return jsonify({'status': 'Data refreshed successfully'})
        else:
            return jsonify({'error': 'Failed to refresh data'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to refresh data: {str(e)}'}), 500

if __name__ == "__main__":
    # Initialize the recommendation system
    initialize_system()
    
    # Start Flask app - use 0.0.0.0 to make it accessible outside container
    app.run(host='0.0.0.0', port=5000)
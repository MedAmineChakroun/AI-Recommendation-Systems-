"""
Main Flask application for recommendation 
"""
from flask import Flask, request, jsonify
import time

# Import project modules
from database import fetch_data_from_db
from models.svd_model import create_svd_model,load_svd_model
from recommender import RecommenderService
from config import DEFAULT_RECOMMENDATIONS

# Initialize Flask app
app = Flask(__name__)

# Global variables for data and model
df = None
recommender_service = None



def initialize_system():
    """Initialize the recommendation system by loading data and training or loading the model"""
    global df, recommender_service

    # Fetch data
    df = fetch_data_from_db()

    if not df.empty:
        # Try to load the model from disk
        svd_model = load_svd_model()

        # If no model exists, train a new one and save it
        if svd_model is None:
            svd_model = create_svd_model(df, save_to_disk=True)

        # Initialize the recommendation service
        recommender_service = RecommenderService(df, svd_model)
        return True
    else:
        return False

@app.route('/recommend', methods=['GET'])
def recommend():

    # Get parameters from request
    user_id = request.args.get('user_id')
    n = int(request.args.get('n', DEFAULT_RECOMMENDATIONS))
    
    if not user_id:
        return jsonify({'error': 'Missing user_id parameter'}), 400
    
    if recommender_service is None:
        return jsonify({'error': 'Recommendation system not initialized'}), 503
    

    response_data = recommender_service.get_top_products(user_id, n)

    return jsonify(response_data)


@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Endpoint to refresh data from the database and retrain the model"""
    start_time = time.time()
    
    success = initialize_system()
    
    if success:
        
        processing_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'success',
            'processing_time_ms': round(processing_time, 2)
        })
    
    return jsonify({'status': 'error'}), 500

if __name__ == "__main__":
    # Initialize the recommendation system
    initialize_system()
    # Start Flask app - use 0.0.0.0 to make it accessible outside container
    app.run(host='0.0.0.0', port=5000)
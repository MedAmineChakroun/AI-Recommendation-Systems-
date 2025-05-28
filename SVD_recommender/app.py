"""
Main Flask application for recommendation with CTR-based model retraining
"""
from flask import Flask, request, jsonify
import time

# Import project modules
from database import fetch_data_from_db
from models.svd_model import create_svd_model, load_svd_model
from recommender import RecommenderService
from config import DEFAULT_RECOMMENDATIONS, Minimum_CTR
from ctr_monitor import get_ctr_last_7_days

# Initialize Flask app
app = Flask(__name__)

# Global variables for data and model
df = None
recommender_service = None
svd_model = None

def initialize_system(force_retrain=False):
    """Initialize the recommendation system by loading data and training or loading the model"""
    global df, recommender_service, svd_model

    # Fetch data
    df = fetch_data_from_db()

    if not df.empty:
        if force_retrain:
            # Force retrain the model
            svd_model = create_svd_model(df, save_to_disk=True)
            print("[SYSTEM] SVD model forcibly retrained")
        else:
            # Try to load the model from disk
            svd_model = load_svd_model()

            # If no model exists, train a new one and save it
            if svd_model is None:
                svd_model = create_svd_model(df, save_to_disk=True)
                print("[SYSTEM] New SVD model trained and saved")

        # Initialize the recommendation service
        recommender_service = RecommenderService(df, svd_model)
        return True
    else:
        return False

def retrain_model():
    """Retrain just the SVD model without reloading data"""
    global df, recommender_service, svd_model
    
    if df is not None and not df.empty:
        # Retrain the model with existing data
        svd_model = create_svd_model(df, save_to_disk=True)
        # Update the recommender service with the new model
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

    
    # Get CTR before refreshing
    ctr = get_ctr_last_7_days()
    print(f"[CTR MONITOR] Weekly CTR = {ctr}")
    
    # Check if CTR is below the minimum threshold
    if ctr is not None:
        if ctr < Minimum_CTR:
            print("[CTR MONITOR] Low CTR detected, refreshing entire recommendation system...")
            success = initialize_system(force_retrain=True)
        else:
            print("[CTR MONITOR] CTR is acceptable, refreshing data only...")
            success = initialize_system(force_retrain=False)
    else:
        print("[CTR MONITOR] CTR could not be retrieved, refreshing data only...")
        success = initialize_system(force_retrain=False)
    
    if success:

        # If CTR is below threshold, model was retrained
        if ctr is not None and ctr < Minimum_CTR:
            message = "CTR is low, model retrained "
            model_status = 'retrained'
        else:
            message = "CTR is acceptable, no refresh needed"
            model_status = 'skipped'
            
        return jsonify({
            'status': model_status,
            'ctr': None if ctr is None else round(ctr, 5),
            'message': message,
        })
    
    return jsonify({'status': 'error'}), 500


@app.route('/force-retrain', methods=['POST'])
def force_retrain_endpoint():
    """Endpoint to force retraining of the model regardless of CTR"""
    start_time = time.time()
    
    print("[FORCE RETRAIN] Forcing model retraining...")
    success = retrain_model()
    
    if success:
        processing_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'success',
            'message': 'Model forcibly retrained',
            'processing_time_ms': round(processing_time, 2)
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrain model (no data available)'
        }), 500
@app.route('/light-refresh', methods=['POST'])
def light_refresh():
    """Lightweight refresh: update df and recommender without retraining"""
    global df, recommender_service

    df = fetch_data_from_db()
    if not df.empty:
        recommender_service.df = df
        recommender_service.user_item_matrix = df.pivot_table(
            index='user_id', columns='item_id', values='rating', fill_value=0
        )
        return jsonify({'status': 'success', 'message': 'Data and user matrix refreshed'})
    else:
        return jsonify({'status': 'error', 'message': 'No data found in DB'}), 500
if __name__ == "__main__":
    # Initialize the recommendation system
    initialize_system()
    # Start Flask app
    app.run(host='0.0.0.0', port=5000)
"""
Main Flask application for recommendation system with performance tracking
"""
from flask import Flask, request, jsonify
import time
import datetime
import threading

# Import project modules
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

# Performance tracking statistics
performance_stats = {
    "api_calls": {
        "recommend": 0,
        "refresh": 0,
        "performance": 0
    },
    "response_times": {
        "recommend": [],
        "refresh": []
    },
    "last_refresh": None,
    "initialization_time": time.time()
}

# Thread lock for thread-safe updates to performance stats
stats_lock = threading.Lock()

def initialize_system():
    """Initialize the recommendation system by loading data and training the model"""
    global df, recommender_service
    
    start_time = time.time()
    
    # Fetch data from database
    df = fetch_data_from_db()
    
    if not df.empty:
        # Create and train the SVD model
        svd_model = create_svd_model(df)
        
        # Initialize the recommender service
        recommender_service = RecommenderService(df, svd_model)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Update performance stats for refresh operation
        with stats_lock:
            performance_stats["last_refresh"] = datetime.datetime.now().isoformat()
            performance_stats["response_times"]["refresh"].append(processing_time)
            if len(performance_stats["response_times"]["refresh"]) > 20:
                performance_stats["response_times"]["refresh"] = performance_stats["response_times"]["refresh"][-20:]
        
        return True
    else:
        return False

@app.route('/recommend', methods=['GET'])
def recommend():
    """Endpoint to get recommendations for a user"""
    start_time = time.time()
    
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
        processing_time = (time.time() - start_time) * 1000
        
        # Update performance stats
        with stats_lock:
            performance_stats["api_calls"]["recommend"] += 1
            performance_stats["response_times"]["recommend"].append(processing_time)
            if len(performance_stats["response_times"]["recommend"]) > 100:
                performance_stats["response_times"]["recommend"] = performance_stats["response_times"]["recommend"][-100:]
                
        return jsonify(cached_result)

    # If not cached, compute recommendations
    response_data = recommender_service.get_top_products(user_id, n)
    
    # Cache the result
    cache_result(cache_key, response_data)
    
    processing_time = (time.time() - start_time) * 1000
    
    # Update performance stats
    with stats_lock:
        performance_stats["api_calls"]["recommend"] += 1
        performance_stats["response_times"]["recommend"].append(processing_time)
        if len(performance_stats["response_times"]["recommend"]) > 100:
            performance_stats["response_times"]["recommend"] = performance_stats["response_times"]["recommend"][-100:]

    return jsonify(response_data)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok' if recommender_service else 'error'})

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Endpoint to refresh data from the database and retrain the model"""
    start_time = time.time()
    
    success = initialize_system()
    
    if success:
        # Flush the cache
        flush_cache()
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update performance stats
        with stats_lock:
            performance_stats["api_calls"]["refresh"] += 1
            performance_stats["response_times"]["refresh"].append(processing_time)
            if len(performance_stats["response_times"]["refresh"]) > 20:
                performance_stats["response_times"]["refresh"] = performance_stats["response_times"]["refresh"][-20:]
            performance_stats["last_refresh"] = datetime.datetime.now().isoformat()
            
        return jsonify({
            'status': 'success',
            'processing_time_ms': round(processing_time, 2)
        })
    
    return jsonify({'status': 'error'}), 500

@app.route('/performance', methods=['GET'])
def get_performance_stats():
    """Endpoint to get performance statistics"""
    with stats_lock:
        performance_stats["api_calls"]["performance"] += 1
        
        # Calculate averages
        avg_recommend_time = sum(performance_stats["response_times"]["recommend"]) / max(len(performance_stats["response_times"]["recommend"]), 1)
        avg_refresh_time = sum(performance_stats["response_times"]["refresh"]) / max(len(performance_stats["response_times"]["refresh"]), 1)
        
        # Calculate uptime
        uptime_seconds = time.time() - performance_stats["initialization_time"]
        
        # Format uptime
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_formatted = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        return jsonify({
            "status": "success",
            "api_calls": performance_stats["api_calls"],
            "average_response_times_ms": {
                "recommend": round(avg_recommend_time, 2),
                "refresh": round(avg_refresh_time, 2)
            },
            "last_refresh": performance_stats["last_refresh"],
            "uptime": uptime_formatted,
            "system_initialized_at": datetime.datetime.fromtimestamp(performance_stats["initialization_time"]).isoformat()
        })

if __name__ == "__main__":
    # Initialize the recommendation system
    initialize_system()

    # Start Flask app - use 0.0.0.0 to make it accessible outside container
    app.run(host='0.0.0.0', port=5000)
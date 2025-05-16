from flask import Flask, request, jsonify
import time
import datetime
import threading
from recommendation import recommendation_engine
from config import DEFAULT_RECOMMENDATIONS

app = Flask(__name__)

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

@app.route('/api/recommend/cart', methods=['POST'])
def recommend():
    start_time = time.time()
    data = request.get_json()

    item_ids_param = data.get('item_ids') if data else None
    count_param = data.get('count') if data else None

    # Default to empty list if item_ids missing or invalid
    if not item_ids_param:
        item_ids = []
    elif isinstance(item_ids_param, list):
        item_ids = [str(item).strip() for item in item_ids_param]
    else:
        item_ids = [item.strip() for item in str(item_ids_param).split(',')]

    # Convert count or fall back to default
    try:
        count = int(count_param) if count_param else DEFAULT_RECOMMENDATIONS
        if count <= 0:
            count = DEFAULT_RECOMMENDATIONS
    except:
        count = DEFAULT_RECOMMENDATIONS

    # Get recommendations
    recommendations = recommendation_engine.get_recommendations(item_ids, count)
    
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    # Update performance stats
    with stats_lock:
        performance_stats["api_calls"]["recommend"] += 1
        performance_stats["response_times"]["recommend"].append(processing_time)
        # Keep only the last 100 response times to avoid unbounded growth
        if len(performance_stats["response_times"]["recommend"]) > 100:
            performance_stats["response_times"]["recommend"] = performance_stats["response_times"]["recommend"][-100:]

    return jsonify({
        "status": "success",
        "input_items": item_ids,
        "recommendations": recommendations,
        "count": len(recommendations),
        "processing_time_ms": round(processing_time, 2),

    })

@app.route('/api/refresh', methods=['POST'])
def refresh():
    start_time = time.time()
    recommendation_engine.initialize()
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Update performance stats
    with stats_lock:
        performance_stats["api_calls"]["refresh"] += 1
        performance_stats["response_times"]["refresh"].append(processing_time)
        if len(performance_stats["response_times"]["refresh"]) > 20:
            performance_stats["response_times"]["refresh"] = performance_stats["response_times"]["refresh"][-20:]
        performance_stats["last_refresh"] = datetime.datetime.now().isoformat()

    return jsonify({
        "status": "success",
        "message": "Recommendation engine refreshed successfully",
        "processing_time_ms": round(processing_time, 2)
    })

@app.route('/api/performance', methods=['GET'])
def get_performance_stats():
    with stats_lock:
        performance_stats["api_calls"]["performance"] += 1
        
        # Calculate averages
        avg_recommend_time = sum(performance_stats["response_times"]["recommend"]) / max(len(performance_stats["response_times"]["recommend"]), 1)
        avg_refresh_time = sum(performance_stats["response_times"]["refresh"]) / max(len(performance_stats["response_times"]["refresh"]), 1)
        
       

        # Calculate uptime
        uptime_seconds = time.time() - performance_stats["initialization_time"]
        
        # Format uptime as days, hours, minutes, seconds
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
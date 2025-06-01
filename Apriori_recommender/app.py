from flask import Flask, request, jsonify
import time
from recommendation import recommendation_engine
from config import DEFAULT_RECOMMENDATIONS , Minimum_CTR
from ctr_monitor import get_ctr_last_7_days

            
app = Flask(__name__)




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

 
   
    return jsonify({
        "status": "success",
        "input_items": item_ids,
        "recommendations": recommendations,
        "count": len(recommendations),
        "processing_time_ms": round(processing_time, 2),

    })
#weekly by n8n
@app.route('/api/refresh', methods=['POST'])
def refresh():
    # get CTR before refreshing
    ctr = get_ctr_last_7_days()
    print(f"[CTR MONITOR] Weekly CTR = {ctr}") 

    # Check if CTR is below the minimum threshold
    if ctr is not None:
        print(f"[CTR MONITOR] Weekly CTR = {ctr}")
        if ctr < Minimum_CTR:
            print("[CTR MONITOR] Low CTR detected, refreshing recommendation engine...")
            start_time = time.time()
            recommendation_engine.initialize()
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return jsonify({
                "status": "retrained",
                "message": "Le moteur de recommandation a bien été mis à jour.",
                "processing_time_ms": round(processing_time, 2)
            })
        else:
            return jsonify({
                "status": "skipped",
                "message": "Le système donne satisfaction, aucun réentraînement n’est requis pour l’instant.",
                "ctr": round(ctr, 5) 
            })
    else:
        return jsonify({
            "status": "error",
            "message": "CTR could not be retrieved (None returned)",
            "ctr": round(ctr, 5)
        })

#force refresh by admin
@app.route('/api/force-refresh', methods=['POST'])
def force_refresh():
    print("[FORCE REFRESH] Forcing recommendation engine refresh...")
    start_time = time.time()
    
    try:
        recommendation_engine.initialize()
        processing_time = (time.time() - start_time) * 1000  # ms
        return jsonify({
            "status": "success",
            "message": "Recommendation engine forcibly refreshed.",
            "processing_time_ms": round(processing_time, 2)
        })
    except Exception as e:
        print(f"[ERROR] Failed to force refresh: {e}")
        return jsonify({
            "status": "error",
            "message": f"Force refresh failed: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
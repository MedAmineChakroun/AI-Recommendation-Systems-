from flask import Flask, request, jsonify
import time
from recommendation import recommendation_engine
from config import DEFAULT_RECOMMENDATIONS

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

    recommendations = recommendation_engine.get_recommendations(item_ids, count)

    return jsonify({
        "status": "success",
        "input_items": item_ids,
        "recommendations": recommendations,
        "count": len(recommendations),
        "processing_time_ms": round((time.time() - start_time) * 1000, 2)
    })

@app.route('/api/refresh', methods=['POST'])
def refresh():
    start_time = time.time()
    recommendation_engine.initialize()
    return jsonify({
        "status": "success",
        "message": "Recommendation engine refreshed successfully",
        "processing_time_ms": round((time.time() - start_time) * 1000, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

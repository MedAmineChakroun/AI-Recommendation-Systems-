"""
Redis cache utility functions
"""
import redis
from config import REDIS_CONFIG, CACHE_TTL

# Initialize Redis client
redis_client = redis.StrictRedis(
    host=REDIS_CONFIG['host'],
    port=REDIS_CONFIG['port'],
    db=REDIS_CONFIG['db'],
    decode_responses=REDIS_CONFIG['decode_responses']
)

def get_cached_result(key):
    """Get result from cache if it exists"""
    try:
        cached_result = redis_client.get(key)
        if cached_result:
            return eval(cached_result)  # Convert string back to dict
        return None
    except Exception as e:
        print(f"Error retrieving from cache: {str(e)}")
        return None

def cache_result(key, data):
    """Cache the result with expiry time"""
    try:
        redis_client.setex(key, CACHE_TTL, str(data))
        return True
    except Exception as e:
        print(f"Error caching result: {str(e)}")
        return False

def flush_cache():
    """Clear all cached data"""
    try:
        redis_client.flushdb()
        return True
    except Exception as e:
        print(f"Error flushing cache: {str(e)}")
        return False
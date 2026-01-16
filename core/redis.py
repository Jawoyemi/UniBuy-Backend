import redis.asyncio as redis
from core.config import settings

redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"WARNING: Could not connect to Redis: {e}")

async def get_redis():
    return redis_client

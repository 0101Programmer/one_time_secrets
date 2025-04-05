import redis
from fastapi import HTTPException

from ..tools.logger_config import setup_logger

logger = setup_logger(__name__)

def get_redis_client():
    try:
        redis_client = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )
        if not redis_client.ping():
            logger.error("Could not connect to Redis")
            raise HTTPException(status_code=500, detail="Could not connect to Redis")
        logger.info("Successfully connected to Redis")
        return redis_client
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")
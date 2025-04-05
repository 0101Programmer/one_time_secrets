import redis
from fastapi import HTTPException

# Подключение к Redis
def get_redis_client():
    try:
        redis_client = redis.Redis(
            host="redis",  # Имя сервиса Redis из docker-compose.yml
            port=6379,
            decode_responses=True  # Автоматически декодирует ответы в строки
        )
        # Проверка подключения
        if not redis_client.ping():
            raise HTTPException(status_code=500, detail="Could not connect to Redis")
        return redis_client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")
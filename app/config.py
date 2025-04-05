from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    # Определение USE_DOCKER
    USE_DOCKER = os.getenv("USE_DOCKER", "0") == "1"

    # Выбор URL базы данных
    if USE_DOCKER:
        DATABASE_URL = os.getenv("DOCKER_POSTGRES_URL")
    else:
        DATABASE_URL = os.getenv("NO_DOCKER_POSTGRES_URL")
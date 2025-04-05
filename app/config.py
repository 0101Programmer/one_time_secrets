from dotenv import load_dotenv
import os
from typing import Optional

# Загрузка переменных окружения из .env файла
load_dotenv()


class Config:
    """
    Класс конфигурации приложения.

    Поля:
        - USE_DOCKER (bool): Флаг использования Docker.
        - DATABASE_URL (Optional[str]): URL базы данных.
    """
    # Определение USE_DOCKER
    USE_DOCKER: bool = os.getenv("USE_DOCKER", "0") == "1"

    def __init__(self):
        """
        Инициализация конфигурации.
        """
        if self.USE_DOCKER:
            self.DATABASE_URL = os.getenv("DOCKER_POSTGRES_URL")
        else:
            self.DATABASE_URL = os.getenv("NO_DOCKER_POSTGRES_URL")

        # Проверка, что DATABASE_URL установлен
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables.")

# Создаём глобальный экземпляр конфигурации
app_config_instance = Config()
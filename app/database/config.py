from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..config import app_config_instance  # Импортируем класс Config


# Используем DATABASE_URL из экземпляра конфигурации
POSTGRES_URL = app_config_instance.DATABASE_URL

# Создаем движок с настройками для Alembic
engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
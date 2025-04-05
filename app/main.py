from fastapi import FastAPI

from app.routes import secrets
from app.tools.secret_cleaner import get_lifespan

app = FastAPI(lifespan=get_lifespan(test_mode=False))

# Подключаем роуты
app.include_router(secrets.router, prefix="/secrets", tags=["secrets"])


from fastapi import FastAPI

from app.routes import secrets
from app.tools.secret_cleaner import register_cleanup_task

app = FastAPI()

# Регистрируем очистку
register_cleanup_task(app)
app.include_router(secrets.router, prefix="/secrets", tags=["secrets"])

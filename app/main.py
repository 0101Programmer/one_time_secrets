from fastapi import FastAPI, Request, Response

from app.routes import secrets
from app.tools.secret_cleaner import get_lifespan

app = FastAPI(lifespan=get_lifespan(test_mode=False))

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Подключаем роуты
app.include_router(secrets.router, prefix="/secrets", tags=["secrets"])


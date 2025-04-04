from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.crud.secrets import create_secret
from ..database import schemas
from ..database.config import get_db

router = APIRouter()

@router.post("/", response_model=schemas.SecretResponse)
async def create_new_secret(
    secret_data: schemas.SecretCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Создает новый секрет. Требуются только secret и passphrase"""
    return create_secret(db, secret_data, request.client.host)
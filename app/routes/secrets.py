import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from ..crud.secrets import create_secret
from ..database import schemas
from ..database.config import get_db
from ..database.models import Secret, SecretLog
from ..database.schemas import SecretReadResponse

router = APIRouter()

@router.post("/", response_model=schemas.SecretResponse)
async def create_new_secret(
    secret_data: schemas.SecretCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    return create_secret(db, secret_data, request.client.host)


@router.get("/secret/{secret_key}", response_model=SecretReadResponse)
async def get_secret(
        secret_key: str,
        passphrase: str,
        request: Request,
        db: Session = Depends(get_db)
):
    # Находим секрет в БД
    secret = db.query(Secret).filter(Secret.secret_key == secret_key).first()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    # Проверяем пароль
    if secret.passphrase != passphrase:
        log = SecretLog(
            secret_id=secret.id,
            secret_key=secret_key,
            action="access_attempt_failed",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Invalid passphrase")

    # Получаем текущее время с часовым поясом
    now = datetime.datetime.now(datetime.timezone.utc)

    # Приводим created_at к aware формату, если он naive
    created_at = secret.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=datetime.timezone.utc)

    # Вычисляем время истечения
    expires_at = created_at + datetime.timedelta(seconds=secret.ttl_seconds)

    # Проверяем срок действия
    if now > expires_at:
        log = SecretLog(
            secret_id=secret.id,
            secret_key=secret_key,
            action="access_attempt_expired",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=410, detail="Secret expired")

    # Проверяем, был ли уже доступ
    if secret.is_accessed:
        log = SecretLog(
            secret_id=secret.id,
            secret_key=secret_key,
            action="access_attempt_already_used",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=410, detail="Secret already accessed")

    # Помечаем как прочитанный и логируем
    secret.is_accessed = True
    log = SecretLog(
        secret_id=secret.id,
        secret_key=secret_key,
        action="access_successful",
        ip_address=request.client.host
    )
    db.add(log)
    db.commit()
    db.refresh(secret)

    return {"secret": secret.secret}
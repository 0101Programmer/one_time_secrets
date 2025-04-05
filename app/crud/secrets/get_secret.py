from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session
from ...database import models
from ...tools.encryption import decrypt_data


def get_secret(
        db: Session,
        secret_key: str,
        passphrase: str,
        ip_address: str
) -> str:
    """
    Получение секрета по ключу с автоматическим удалением истёкших
    Возвращает:
        - str: содержимое секрета при успехе
    Вызывает:
        - HTTPException: при различных ошибках доступа
    """
    # Находим секрет в БД (включая проверку на удаление)
    secret = db.query(models.Secret).filter(
        models.Secret.secret_key == secret_key,
        models.Secret.is_deleted == False
    ).first()

    if not secret:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    # Дешифруем пароль для проверки
    try:
        decrypted_passphrase = decrypt_data(secret.encrypted_passphrase)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decrypting passphrase"
        )

    # Проверяем пароль
    if decrypted_passphrase != passphrase:
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_failed",
            ip_address
        )
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid passphrase"
        )

    # Проверяем срок действия
    now = datetime.now(timezone.utc)
    created_at = secret.created_at.replace(
        tzinfo=timezone.utc) if secret.created_at.tzinfo is None else secret.created_at
    expires_at = created_at + timedelta(seconds=secret.ttl_seconds)

    if now > expires_at:
        # Автоматически помечаем как удалённый
        secret.is_deleted = True

        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "auto_delete_expired_on_access",
            ip_address
        )
        db.commit()

        raise HTTPException(
            status_code=http_status.HTTP_410_GONE,
            detail="Secret expired and has been automatically deleted"
        )

    # Проверяем, был ли уже доступ
    if secret.is_accessed:
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_already_used",
            ip_address
        )
        raise HTTPException(
            status_code=http_status.HTTP_410_GONE,
            detail="Secret already accessed"
        )

    # Дешифруем секрет
    try:
        decrypted_secret = decrypt_data(secret.encrypted_secret)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decrypting secret"
        )

    # Помечаем как прочитанный
    secret.is_accessed = True
    _log_access_attempt(
        db,
        secret.id,
        secret_key,
        "access_successful",
        ip_address
    )
    db.commit()

    return decrypted_secret


def _log_access_attempt(
        db: Session,
        secret_id: int | None,
        secret_key: str,
        action: str,
        ip_address: str
) -> None:
    """Вспомогательная функция для логирования попыток доступа"""
    log = models.SecretLog(
        secret_id=secret_id,
        secret_key=secret_key,
        action=action,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
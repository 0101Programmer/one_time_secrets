from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ...cache.redis_config import get_redis_client
from ...database import models
from ...tools.encryption import decrypt_data
from ...tools.logger_config import setup_logger

logger = setup_logger(__name__)

def get_secret(
        db: Session,
        secret_key: str,
        passphrase: Optional[str] = None,
        ip_address: str = "unknown"
) -> str:
    """
    Получение секрета по ключу с автоматическим удалением истёкших.

    Параметры:
        - db (Session): Сессия базы данных SQLAlchemy.
        - secret_key (str): Уникальный ключ секрета.
        - passphrase (Optional[str]): Опциональный пароль для доступа к секрету.
        - ip_address (str): IP-адрес клиента, запрашивающего секрет.

    Возвращает:
        - str: Содержимое секрета при успехе.

    Вызывает:
        - HTTPException:
            - 404 Not Found: Если секрет не найден.
            - 403 Forbidden: Если пароль неверен.
            - 410 Gone: Если секрет уже был получен или истек срок его действия.
            - 500 Internal Server Error: При ошибке дешифрования.
    """
    try:
        redis_client = get_redis_client()  # Получаем клиент Redis

        # Проверяем наличие секрета в Redis
        encrypted_secret = redis_client.get(f"secret:{secret_key}")
        encrypted_passphrase = redis_client.get(f"passphrase:{secret_key}")

        if encrypted_secret:
            # Удаляем секрет и пароль из Redis после чтения
            redis_client.delete(f"secret:{secret_key}")
            if encrypted_passphrase:
                redis_client.delete(f"passphrase:{secret_key}")

            # Проверяем пароль, если он существует
            if encrypted_passphrase:
                decrypted_passphrase = decrypt_data(encrypted_passphrase)
                if decrypted_passphrase != passphrase:
                    _log_access_attempt(
                        db,
                        None,
                        secret_key,
                        "access_attempt_failed",
                        ip_address
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid passphrase"
                    )
            elif passphrase is not None:
                _log_access_attempt(
                    db,
                    None,
                    secret_key,
                    "access_attempt_failed",
                    ip_address
                )
                raise HTTPException(
                    status_code=403,
                    detail="Passphrase was not set for this secret"
                )

            # Дешифруем и возвращаем секрет
            return decrypt_data(encrypted_secret)

    except Exception as e:
        # Если Redis недоступен, логируем ошибку и продолжаем работу
        logger.error(f"Redis error during secret retrieval: {e}")

    # === Шаг 1: Поиск секрета в БД ===
    secret = db.query(models.Secret).filter(
        models.Secret.secret_key == secret_key,
        models.Secret.is_deleted == False
    ).first()

    if not secret:
        raise HTTPException(
            status_code=404,
            detail="Secret not found"
        )

    # === Шаг 2: Проверка пароля ===
    if secret.encrypted_passphrase:
        decrypted_passphrase = decrypt_data(secret.encrypted_passphrase)
        if decrypted_passphrase != passphrase:
            _log_access_attempt(
                db,
                secret.id,
                secret_key,
                "access_attempt_failed",
                ip_address
            )
            raise HTTPException(
                status_code=403,
                detail="Invalid passphrase"
            )
    elif passphrase is not None:
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_failed",
            ip_address
        )
        raise HTTPException(
            status_code=403,
            detail="Passphrase was not set for this secret"
        )

    # === Шаг 3: Проверка срока действия секрета ===
    now = datetime.now(timezone.utc)
    created_at = secret.created_at.replace(
        tzinfo=timezone.utc) if secret.created_at.tzinfo is None else secret.created_at
    expires_at = created_at + timedelta(seconds=secret.ttl_seconds)

    if now > expires_at:
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
            status_code=410,
            detail="Secret expired and has been automatically deleted"
        )

    # === Шаг 4: Проверка, был ли уже доступ ===
    if secret.is_accessed:
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_already_used",
            ip_address
        )
        raise HTTPException(
            status_code=410,
            detail="Secret already accessed"
        )

    # === Шаг 5: Дешифрование секрета ===
    try:
        decrypted_secret = decrypt_data(secret.encrypted_secret)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error decrypting secret"
        )

    # === Шаг 6: Пометка секрета как прочитанного ===
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
    """
    Вспомогательная функция для логирования попыток доступа к секрету.

    Параметры:
        - db (Session): Сессия базы данных SQLAlchemy.
        - secret_id (int | None): ID секрета (если доступен).
        - secret_key (str): Уникальный ключ секрета.
        - action (str): Действие, которое необходимо зафиксировать (например, "access_successful").
        - ip_address (str): IP-адрес клиента, совершающего действие.
    """
    log = models.SecretLog(
        secret_id=secret_id,
        secret_key=secret_key,
        action=action,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
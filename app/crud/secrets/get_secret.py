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
    Получение секрета по ключу с автоматическим удалением истёкших.

    Параметры:
        - db (Session): Сессия базы данных SQLAlchemy.
        - secret_key (str): Уникальный ключ секрета.
        - passphrase (str): Пароль для доступа к секрету.
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
    # === Шаг 1: Поиск секрета в БД ===
    # Ищем секрет по secret_key и проверяем, что он не помечен как удалённый.
    secret = db.query(models.Secret).filter(
        models.Secret.secret_key == secret_key,
        models.Secret.is_deleted == False
    ).first()

    if not secret:
        # Если секрет не найден, выбрасываем ошибку 404.
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    # === Шаг 2: Дешифрование пароля ===
    # Дешифруем зашифрованный пароль из базы данных для проверки.
    try:
        decrypted_passphrase = decrypt_data(secret.encrypted_passphrase)
    except Exception as e:
        # Если возникла ошибка при дешифровании пароля, выбрасываем 500.
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decrypting passphrase"
        )

    # === Шаг 3: Проверка пароля ===
    # Сравниваем дешифрованный пароль с переданным клиентом.
    if decrypted_passphrase != passphrase:
        # Логируем попытку доступа с неверным паролем.
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_failed",
            ip_address
        )
        # Выбрасываем ошибку 403, если пароль неверен.
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid passphrase"
        )

    # === Шаг 4: Проверка срока действия секрета ===
    # Вычисляем время истечения срока действия секрета.
    now = datetime.now(timezone.utc)
    created_at = secret.created_at.replace(
        tzinfo=timezone.utc) if secret.created_at.tzinfo is None else secret.created_at
    expires_at = created_at + timedelta(seconds=secret.ttl_seconds)

    if now > expires_at:
        # Если срок действия истёк, помечаем секрет как удалённый.
        secret.is_deleted = True

        # Логируем автоматическое удаление истекшего секрета.
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "auto_delete_expired_on_access",
            ip_address
        )
        db.commit()

        # Выбрасываем ошибку 410, если секрет истёк.
        raise HTTPException(
            status_code=http_status.HTTP_410_GONE,
            detail="Secret expired and has been automatically deleted"
        )

    # === Шаг 5: Проверка, был ли уже доступ ===
    # Проверяем, был ли секрет уже получен ранее.
    if secret.is_accessed:
        # Логируем попытку повторного доступа.
        _log_access_attempt(
            db,
            secret.id,
            secret_key,
            "access_attempt_already_used",
            ip_address
        )
        # Выбрасываем ошибку 410, если секрет уже был получен.
        raise HTTPException(
            status_code=http_status.HTTP_410_GONE,
            detail="Secret already accessed"
        )

    # === Шаг 6: Дешифрование секрета ===
    # Дешифруем содержимое секрета.
    try:
        decrypted_secret = decrypt_data(secret.encrypted_secret)
    except Exception as e:
        # Если возникла ошибка при дешифровании секрета, выбрасываем 500.
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decrypting secret"
        )

    # === Шаг 7: Пометка секрета как прочитанного ===
    # Помечаем секрет как прочитанный, чтобы предотвратить повторный доступ.
    secret.is_accessed = True

    # Логируем успешное получение секрета.
    _log_access_attempt(
        db,
        secret.id,
        secret_key,
        "access_successful",
        ip_address
    )
    db.commit()

    # Возвращаем дешифрованное содержимое секрета.
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
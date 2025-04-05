from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ...cache.redis_config import get_redis_client
from ...database import models
from ...tools.logger_config import setup_logger

logger = setup_logger(__name__)

def delete_secret(
        db: Session,  # Сессия базы данных SQLAlchemy
        secret_key: str,  # Уникальный ключ секрета
        ip_address: str  # IP-адрес клиента, запрашивающего удаление
) -> Tuple[bool, Optional[int]]:  # Возвращает кортеж (успех/неудача, ID секрета или None)
    """
    Мягкое удаление секрета.

    Параметры:
        - db (Session): Сессия базы данных SQLAlchemy.
        - secret_key (str): Уникальный ключ секрета.
        - ip_address (str): IP-адрес клиента, запрашивающего удаление.

    Возвращает:
        - Tuple[bool, int | None]:
            - (True, secret_id): Если удаление успешно.
            - (False, None): Если секрет не найден.
            - (False, secret_id): Если секрет уже удалён.
    """
    # === Шаг 1: Поиск секрета в БД ===
    # Ищем секрет по secret_key.
    secret = db.query(models.Secret).filter(
        models.Secret.secret_key == secret_key
    ).first()

    if not secret:
        # Если секрет не найден, возвращаем (False, None).
        return False, None

    # === Шаг 2: Проверка, был ли секрет уже удалён ===
    # Если секрет уже помечен как удалённый, возвращаем (False, secret_id).
    if secret.is_deleted:
        return False, secret.id

    # === Шаг 3: Удаление секрета из Redis ===
    try:
        redis_client = get_redis_client()  # Получаем клиент Redis
        redis_client.delete(secret_key)  # Удаляем секрет из Redis
    except Exception as e:
        # Если Redis недоступен, логируем ошибку, но продолжаем работу
        logger.error(f"Redis error during secret deletion: {e}")

    # === Шаг 4: Мягкое удаление ===
    # Помечаем секрет как удалённый (is_deleted = True).
    secret.is_deleted = True

    # === Шаг 5: Логирование успешного удаления ===
    # Создаём запись в логе об успешном удалении.
    log = models.SecretLog(
        secret_id=secret.id,
        secret_key=secret_key,
        action="delete_successful",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    # === Шаг 6: Возвращаем результат ===
    # Возвращаем (True, secret_id) для подтверждения успешного удаления.
    return True, secret.id
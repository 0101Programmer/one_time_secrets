from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Tuple
from ...database import models


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

    # === Шаг 3: Мягкое удаление ===
    # Помечаем секрет как удалённый (is_deleted = True).
    secret.is_deleted = True

    # === Шаг 4: Логирование успешного удаления ===
    # Создаём запись в логе об успешном удалении.
    log = models.SecretLog(
        secret_id=secret.id,
        secret_key=secret_key,
        action="delete_successful",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    # === Шаг 5: Возвращаем результат ===
    # Возвращаем (True, secret_id) для подтверждения успешного удаления.
    return True, secret.id
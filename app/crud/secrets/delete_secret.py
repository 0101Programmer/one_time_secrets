from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ...database import models

def delete_secret(
    db: Session,
    secret_key: str,
    ip_address: str
) -> tuple[bool, int | None]:
    """
    Мягкое удаление секрета.
    Возвращает:
        - (True, secret_id): если удаление успешно
        - (False, None): если секрет не найден
        - (False, secret_id): если секрет уже удалён
    """
    secret = db.query(models.Secret).filter(
        models.Secret.secret_key == secret_key
    ).first()

    if not secret:
        return (False, None)

    if secret.is_deleted:
        return (False, secret.id)

    secret.is_deleted = True
    secret.deleted_at = datetime.now(timezone.utc)

    log = models.SecretLog(
        secret_id=secret.id,
        secret_key=secret_key,
        action="delete_successful",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    return (True, secret.id)
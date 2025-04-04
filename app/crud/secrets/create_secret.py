from sqlalchemy.orm import Session

from ...database import schemas, models


def create_secret(db: Session, secret_data: schemas.SecretCreate, ip_address: str):
    # Создаем объект Secret (остальные поля заполнятся автоматически)
    db_secret = models.Secret(
        secret=secret_data.secret,
        passphrase=secret_data.passphrase,
        ttl_seconds=secret_data.ttl_seconds
    )

    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)

    # Логируем создание
    log = models.SecretLog(
        secret_id=db_secret.id,
        secret_key=db_secret.secret_key,
        action="create",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    return db_secret
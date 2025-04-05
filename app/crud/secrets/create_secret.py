from sqlalchemy.orm import Session

from ...database import schemas, models


def create_secret(db: Session, secret_data: schemas.SecretCreate, ip_address: str) -> schemas.SecretResponse:
    # Создание нового секрета
    db_secret = models.Secret(
        ttl_seconds=secret_data.ttl_seconds
    )

    # Шифрование и сохранение секрета и пароля
    db_secret.set_secret(secret=secret_data.secret, passphrase=secret_data.passphrase)

    # Добавление секрета в базу данных
    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)

    # Логирование создания секрета
    log = models.SecretLog(
        secret_id=db_secret.id,
        secret_key=db_secret.secret_key,
        action="secret_created",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    # Возвращаем ответ с ключом доступа к секрету
    return schemas.SecretResponse(secret_key=db_secret.secret_key)
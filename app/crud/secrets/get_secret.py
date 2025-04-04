from sqlalchemy.orm import Session
from ...database.models import Secret, SecretLog
from fastapi import HTTPException


def get_secret(db: Session, secret_key: str, ip_address: str):
    secret = db.query(Secret).filter(Secret.secret_key == secret_key).first()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    if not secret.is_accessed:
        secret.is_accessed = True
        log = SecretLog(
            secret_id=secret.id,
            secret_key=secret.secret_key,
            action="first_read",
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(secret)

    return secret
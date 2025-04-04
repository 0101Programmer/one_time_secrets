from sqlalchemy.orm import Session
from ...database.models import Secret, SecretLog

def get_logs_by_secret(db: Session, secret_key: str):
    return db.query(SecretLog).filter(SecretLog.secret_key == secret_key).all()
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..database import models
from ..database.config import SessionLocal


def clean_expired_secrets(batch_size: int = 100) -> dict:
    """
    Очистка истёкших секретов
    Возвращает:
        {
            "deleted_count": int,
            "status": "success"|"partial"|"error",
            "message": str
        }
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_secrets = db.query(models.Secret).filter(
            models.Secret.is_deleted == False,
            models.Secret.created_at + timedelta(seconds=models.Secret.ttl_seconds) < now
        ).limit(batch_size).all()

        deleted_count = 0
        for secret in expired_secrets:
            secret.is_deleted = True
            secret.deleted_at = now

            # Логируем автоматическое удаление
            log = models.SecretLog(
                secret_id=secret.id,
                secret_key=secret.secret_key,
                action="auto_cleanup_expired",
                ip_address="system"
            )
            db.add(log)
            deleted_count += 1

        db.commit()

        return {
            "deleted_count": deleted_count,
            "status": "success",
            "message": f"Deleted {deleted_count} expired secrets"
        }

    except Exception as e:
        db.rollback()
        return {
            "deleted_count": 0,
            "status": "error",
            "message": f"Cleanup failed: {str(e)}"
        }
    finally:
        db.close()


def register_cleanup_task(app):
    """Регистрация периодической задачи в приложении"""

    @app.on_event("startup")
    async def startup_cleanup():
        # Запускаем сразу при старте
        clean_expired_secrets()

    @app.on_event("startup")
    async def schedule_cleanup():
        # Здесь можно подключить планировщик (APScheduler, Celery и т.д.)
        pass
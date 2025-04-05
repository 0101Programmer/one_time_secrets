import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator, Dict

from fastapi import FastAPI
from sqlalchemy import func, types

from .logger_config import setup_logger
from ..database import models
from ..database.config import SessionLocal

# Настройка логгера для этого модуля
logger = setup_logger(__name__)


def clean_expired_secrets(batch_size: int = 100) -> Dict:
    """
    Очистка истёкших секретов
    """
    db = SessionLocal()
    deleted_count = 0

    try:
        now = datetime.now(timezone.utc)
        logger.info(f"Starting cleanup at {now.isoformat()}")

        # Получаем текущее время из БД для проверки
        db_now = db.query(func.now()).scalar()
        logger.info(f"Database current time: {db_now}")

        # Загружаем все активные секреты (не удалённые)
        all_secrets = db.query(models.Secret).filter(
            models.Secret.is_deleted == False
        ).all()

        logger.info(f"Loaded {len(all_secrets)} secrets for processing")

        # Фильтруем истёкшие секреты на стороне Python
        expired_secrets = [
            secret for secret in all_secrets
            if secret.created_at + timedelta(seconds=secret.ttl_seconds) < now
        ]

        logger.info(f"Found {len(expired_secrets)} expired secrets")

        for secret in expired_secrets[:batch_size]:  # Обрабатываем только batch_size секретов
            expires_at = secret.created_at + timedelta(seconds=secret.ttl_seconds)
            logger.info(
                f"Deleting secret ID={secret.id}: "
                f"created={secret.created_at}, "
                f"ttl={secret.ttl_seconds}s, "
                f"expired_at={expires_at}"
            )

            secret.is_deleted = True

            log = models.SecretLog(
                secret_id=secret.id,
                secret_key=secret.secret_key,
                action="auto_cleanup_expired",
                ip_address="system"
            )
            db.add(log)
            deleted_count += 1

        db.commit()
        logger.info(f"Successfully deleted {deleted_count} secrets")
        return {
            "deleted_count": deleted_count,
            "status": "success",
            "message": f"Deleted {deleted_count} expired secrets"
        }

    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "deleted_count": 0,
            "status": "error",
            "message": f"Cleanup failed: {str(e)}"
        }
    finally:
        db.close()
        logger.info("Cleanup session closed")


def get_lifespan(test_mode: bool = False) -> AsyncIterator[None]:
    """
    Lifespan менеджер с возможностью тестирования
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting background cleanup task")

        # Для тестов можно использовать интервал 5 секунд
        interval = 5 if test_mode else 3600
        logger.info(f"Cleanup interval set to {interval} seconds")

        task = asyncio.create_task(periodic_cleanup(interval))

        try:
            yield
        finally:
            logger.info("Stopping background task")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Background task cancelled successfully")
            except Exception as e:
                logger.error(f"Error during task cancellation: {e}")

    return lifespan


async def periodic_cleanup(interval: int):
    """Фоновая задача очистки с заданным интервалом"""
    logger.info(f"Periodic cleanup task started (interval: {interval}s)")

    while True:
        try:
            start_time = datetime.now(timezone.utc)
            logger.info("Starting cleanup cycle")

            result = await asyncio.to_thread(clean_expired_secrets)
            logger.info(f"Cleanup result: {result}")

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Cleanup completed in {duration:.2f} seconds")

            logger.info(f"Waiting {interval} seconds before next cleanup")
            await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}", exc_info=True)
            await asyncio.sleep(min(60, interval))  # Ждём перед повторной попыткой
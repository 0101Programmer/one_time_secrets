from sqlalchemy.orm import Session
from ...database import schemas, models
from ...cache.redis_config import get_redis_client
from ...tools.logger_config import setup_logger

logger = setup_logger(__name__)


def create_secret(
        db: Session,  # Сессия базы данных SQLAlchemy
        secret_data: schemas.SecretCreate,  # Данные для создания секрета (из Pydantic-схемы)
        ip_address: str  # IP-адрес клиента, создающего секрет
) -> schemas.SecretResponse:  # Возвращаемый объект (Pydantic-схема)
    """
    Создание нового секрета.

    Параметры:
        - db (Session): Сессия базы данных SQLAlchemy.
        - secret_data (schemas.SecretCreate): Данные для создания секрета (secret, passphrase, ttl_seconds).
        - ip_address (str): IP-адрес клиента, создающего секрет.

    Возвращает:
        - schemas.SecretResponse: Ответ с уникальным ключом доступа к секрету.
    """
    # === Шаг 1: Создание нового секрета ===
    # Создаём экземпляр модели Secret с указанием времени жизни (ttl_seconds).
    db_secret = models.Secret(
        ttl_seconds=secret_data.ttl_seconds  # TTL может быть None, если не указано
    )

    # === Шаг 2: Шифрование и сохранение секрета и пароля ===
    # Используем метод set_secret для шифрования и сохранения секрета и пароля.
    db_secret.set_secret(
        secret=secret_data.secret,  # Конфиденциальные данные
        passphrase=secret_data.passphrase  # Опциональный пароль
    )

    # === Шаг 3: Добавление секрета в базу данных ===
    # Добавляем секрет в базу данных и фиксируем изменения.
    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)  # Обновляем объект db_secret, чтобы получить все поля из БД

    # === Шаг 4: Сохранение секрета в Redis ===
    try:
        redis_client = get_redis_client()  # Получаем клиент Redis
        redis_client.set(
            db_secret.secret_key,  # Ключ для Redis (уникальный ключ секрета)
            db_secret.encrypted_secret,  # Зашифрованный секрет
            ex=300  # TTL = 5 минут (300 секунд)
        )
    except Exception as e:
        # Если Redis недоступен, логируем ошибку, но продолжаем работу
        logger.error(f"Redis error: {e}")

    # === Шаг 5: Логирование создания секрета ===
    # Создаём запись в логе о создании секрета.
    log = models.SecretLog(
        secret_id=db_secret.id,  # ID созданного секрета
        secret_key=db_secret.secret_key,  # Уникальный ключ секрета
        action="secret_created",  # Действие: "создание секрета"
        ip_address=ip_address  # IP-адрес клиента
    )
    db.add(log)
    db.commit()

    # === Шаг 6: Возвращение ответа ===
    # Возвращаем объект SecretResponse с уникальным ключом доступа к секрету.
    return schemas.SecretResponse(secret_key=db_secret.secret_key)
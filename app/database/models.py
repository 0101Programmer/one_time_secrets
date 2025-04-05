from datetime import datetime, timezone
import secrets

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional

from .config import Base
from ..tools.encryption import encrypt_data, decrypt_data


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    encrypted_secret = Column(String, nullable=False)  # Храним зашифрованный секрет
    encrypted_passphrase = Column(String, nullable=True)  # Опциональный зашифрованный пароль
    ttl_seconds = Column(Integer, default=3600)  # Время жизни секрета (по умолчанию 3600 секунд)
    secret_key = Column(String, index=True, unique=True, default=lambda: secrets.token_urlsafe(16))  # Уникальный ключ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # Время создания
    is_accessed = Column(Boolean, default=False)  # Флаг доступа
    is_deleted = Column(Boolean, default=False)  # Флаг удаления
    logs = relationship("SecretLog", back_populates="secret_ref", cascade="all, delete-orphan")  # Логи

    def set_secret(self, secret: str, passphrase: Optional[str] = None):
        """
        Шифрует и сохраняет секрет и пароль.

        Параметры:
            - secret (str): Конфиденциальные данные.
            - passphrase (Optional[str]): Опциональный пароль.
        """
        self.encrypted_secret = encrypt_data(secret)
        self.encrypted_passphrase = encrypt_data(passphrase) if passphrase else None

    def get_secret(self) -> tuple:
        """
        Дешифрует и возвращает секрет и пароль.

        Возвращает:
            - tuple: (секрет, пароль). Пароль может быть None, если его нет.
        """
        secret = decrypt_data(self.encrypted_secret)
        passphrase = decrypt_data(self.encrypted_passphrase) if self.encrypted_passphrase else None
        return secret, passphrase


class SecretLog(Base):
    """
    Модель для логирования действий с секретами.

    Поля:
        - id: Уникальный идентификатор записи.
        - secret_id: ID секрета (может быть NULL, если секрет удалён).
        - secret_key: Уникальный ключ секрета.
        - action: Действие (например, "create", "delete", "access").
        - ip_address: IP-адрес клиента.
        - created_at: Время создания записи.
    """
    __tablename__ = "secret_logs"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор записи
    secret_id = Column(
        Integer,
        ForeignKey('secrets.id'),
        nullable=True
    )  # ID секрета (может быть NULL)
    secret_key = Column(String, index=True)  # Уникальный ключ секрета
    action = Column(String)  # Действие (например, "create", "delete", "access")
    ip_address = Column(String)  # IP-адрес клиента
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )  # Время создания записи

    secret_ref = relationship("Secret", back_populates="logs")  # Связь с моделью Secret
from datetime import datetime, timezone
import secrets

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .config import Base
from ..tools.encryption import encrypt_data, decrypt_data


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    encrypted_secret = Column(String, nullable=False)  # Храним зашифрованный секрет
    encrypted_passphrase = Column(String, nullable=False)  # Храним зашифрованный пароль
    ttl_seconds = Column(Integer, default=3600)
    secret_key = Column(String, index=True, unique=True, default=lambda: secrets.token_urlsafe(16))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_accessed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    logs = relationship("SecretLog", back_populates="secret_ref", cascade="all, delete-orphan")

    def set_secret(self, secret: str, passphrase: str):
        """
        Шифрует и сохраняет секрет и пароль.
        """
        self.encrypted_secret = encrypt_data(secret)
        self.encrypted_passphrase = encrypt_data(passphrase)

    def get_secret(self) -> tuple:
        """
        Дешифрует и возвращает секрет и пароль.
        """
        secret = decrypt_data(self.encrypted_secret)
        passphrase = decrypt_data(self.encrypted_passphrase)
        return secret, passphrase


class SecretLog(Base):
    __tablename__ = "secret_logs"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(Integer, ForeignKey('secrets.id'), nullable=True)
    secret_key = Column(String, index=True)
    action = Column(String)
    ip_address = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    secret_ref = relationship("Secret", back_populates="logs")
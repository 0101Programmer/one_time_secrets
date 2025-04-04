import datetime
import secrets

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .config import Base


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    secret = Column(String, nullable=False)
    passphrase = Column(String, nullable=False)
    ttl_seconds = Column(Integer, default=3600)  # 1 час по умолчанию
    secret_key = Column(String, index=True, unique=True, default=lambda: secrets.token_urlsafe(16))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    is_accessed = Column(Boolean, default=False)
    logs = relationship("SecretLog", back_populates="secret_ref", cascade="all, delete-orphan")


class SecretLog(Base):
    __tablename__ = "secret_logs"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(Integer, ForeignKey('secrets.id'), nullable=True)
    secret_key = Column(String, index=True)
    action = Column(String)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    secret_ref = relationship("Secret", back_populates="logs")
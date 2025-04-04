from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SecretBase(BaseModel):
    secret: str
    passphrase: str
    ttl_seconds: Optional[int] = 3600  # Значение по умолчанию 1 час


class SecretCreate(SecretBase):
    pass


class SecretResponse(SecretBase):
    id: int
    secret_key: str
    created_at: datetime
    is_accessed: bool

    class Config:
        from_attributes = True


class SecretLogResponse(BaseModel):
    id: int
    secret_id: Optional[int]
    secret_key: str
    action: str
    ip_address: str
    created_at: datetime

    class Config:
        from_attributes = True
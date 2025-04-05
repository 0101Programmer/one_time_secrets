from pydantic import BaseModel, validator, field_validator
from datetime import datetime
from typing import Optional


class SecretBase(BaseModel):
    secret: str # обязательный параметр
    passphrase: Optional[str] = None  # passphrase  - опциональный параметр
    ttl_seconds: Optional[int] = 3600  # Значение по умолчанию 1 час (опциональный параметр)

    model_config = {
        "json_schema_extra": {
            "example": {
                "secret": "доступ_к_конфиденциальным_данным",
                "passphrase": "my_passphrase",
                "ttl_seconds": 3600
            }
        }
    }

    @field_validator("ttl_seconds")
    def validate_ttl_seconds(cls, value):
        """
        Валидация ttl_seconds:
        - Если значение указано, оно должно быть больше 0.
        - Если значение не указано, используется значение по умолчанию (3600).
        """
        if value is not None and value <= 0:
            raise ValueError("ttl_seconds must be greater than 0.")
        return value

class SecretCreate(SecretBase):
    pass


class SecretResponse(BaseModel):
    secret_key: str


class SecretReadResponse(BaseModel):
    secret: str


class SecretDeleteResponse(BaseModel):
    status: str
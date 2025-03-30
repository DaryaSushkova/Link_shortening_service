from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
import re


class LinkCreate(BaseModel):
    original_url: str
    # Необязательные параметры
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("original_url")
    @classmethod
    def validate_original_url(cls, v):
        """
        Использование валидатора, а не HttpUrl,
        чтобы не возникало проблем с кодировкой кириллицы.
        """
        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL must start with http:// or https://!")
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain!")
        return v
    
    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, v):
        """
        В кастомный алиас можно вводить только цифры и буквы,
        чтобы не возникало проблем со спец. символами
        """
        if v is None:
            return v
        if not re.fullmatch(r"[A-Za-zА-Яа-я0-9]+", v):
            raise ValueError("Custom alias must contain only letters and digits!")
        return v


class LinkRead(BaseModel):
    short_code: str
    original_url: str

    model_config = ConfigDict(from_attributes=True)


class LinkUpdate(BaseModel):
    original_url: str

    @field_validator("original_url")
    @classmethod
    def validate_original_url(cls, v):
        """
        Использование валидатора, а не HttpUrl,
        чтобы не возникало проблем с кодировкой кириллицы.
        """
        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL must start with http:// or https://!")
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain!")
        return v


class LinkStats(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    clicks_count: int
    last_clicked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

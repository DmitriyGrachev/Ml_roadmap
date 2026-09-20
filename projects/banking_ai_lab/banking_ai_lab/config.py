"""Environment-backed configuration for the Banking AI Lab application."""

from __future__ import annotations

from typing import ClassVar

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings loaded from ``BANKING_*`` variables."""

    model_config = SettingsConfigDict(
        env_prefix="BANKING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    KNOWN_LOG_LEVELS: ClassVar[frozenset[str]] = frozenset(
        {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    )

    database_url: str = "sqlite:///./banking_ai_lab.db"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    @field_validator("database_url")
    @classmethod
    def require_database_url(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("database URL must be nonblank and contain no outer whitespace")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_known_log_level(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("log level must contain no outer whitespace")
        normalized = value.upper()
        if normalized not in cls.KNOWN_LOG_LEVELS:
            raise ValueError("unknown log level")
        return normalized

    @field_validator("api_prefix")
    @classmethod
    def require_absolute_api_prefix(cls, value: str) -> str:
        if (
            not value.startswith("/")
            or value == "/"
            or value.endswith("/")
            or value.startswith("//")
            or value != value.strip()
        ):
            raise ValueError("API prefix must be an absolute path without a trailing slash")
        return value

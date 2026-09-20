from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class SupportSettings(BaseSettings):
    """Environment-backed configuration owned by the application boundary."""

    model_config = SettingsConfigDict(
        env_prefix="SUPPORT_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "support-api"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

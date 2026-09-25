"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MIRROR-X"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = "mysql+aiomysql://mirrorx:mirrorxpassword@localhost:3306/mirrorx"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    allowed_hosts: list[str] = ["*"]

    # Security & Authentication
    secret_key: str = "mirrorx-dev-secret-key-change-in-prod"
    api_keys: list[str] = ["mirrorx-dev-api-key"]
    secure_cookies: bool = True
    max_upload_size_bytes: int = 15_728_640  # 15 MB

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_sensitive_per_minute: int = 30

    # Observability & Tracing
    telemetry_enabled: bool = True
    telemetry_sample_rate: float = 1.0

    # Model Context Protocol (MCP)
    mcp_enabled: bool = True
    mcp_auth_required: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

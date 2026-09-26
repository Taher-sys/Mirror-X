"""Tests for application configuration."""

from app.core.config import Settings, get_settings


def test_settings_defaults():
    """Test that settings have correct defaults."""
    settings = Settings(_env_file=None)

    assert settings.app_name == "MIRROR-X"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.environment == "development"


def test_settings_database_url_default(monkeypatch):
    """Test that database URL has a default value."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)

    assert "mysql+aiomysql" in settings.database_url


def test_get_settings_returns_cached_instance():
    """Test that get_settings returns a cached settings instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_cors_origins_default():
    """Test that CORS origins default includes localhost."""
    settings = Settings(_env_file=None)

    assert "http://localhost:3000" in settings.cors_origins

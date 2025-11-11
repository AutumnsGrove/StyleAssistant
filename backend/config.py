"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables or secrets.json file.
Supports validation and type conversion.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Loads from environment variables or secrets.json with validation.
    All sensitive data (API keys) should be stored in secrets.json which
    is excluded from version control.
    """

    model_config = SettingsConfigDict(
        env_file="secrets.json",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key for Claude models"
    )

    # Database Configuration
    database_path: str = Field(
        default="backend/style_assistant.db", description="SQLite database file path"
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["moz-extension://*"], description="Allowed CORS origins"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    @classmethod
    def load_from_secrets_json(cls, secrets_path: Optional[Path] = None):
        """
        Load settings from secrets.json file.

        Args:
            secrets_path: Path to secrets.json file (default: project root)

        Returns:
            Settings instance
        """
        if secrets_path is None:
            secrets_path = Path(__file__).parent.parent / "secrets.json"

        if secrets_path.exists():
            with open(secrets_path) as f:
                data = json.load(f)
            return cls(**data)
        else:
            # Try environment variables
            return cls()


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are loaded only once.
    Can be used as FastAPI dependency.

    Returns:
        Settings: Cached settings instance
    """
    return Settings.load_from_secrets_json()

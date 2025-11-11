"""
Dependency injection functions for FastAPI.

Provides reusable dependencies for database connections, settings,
and AI providers.
"""

from typing import Optional

from functools import lru_cache

from backend.config import get_settings, Settings
from backend.database import get_db
from backend.ai_providers.base import AIProvider
from backend.ai_providers.claude import ClaudeProvider


# Re-export for convenience
__all__ = ["get_db", "get_settings", "get_ai_provider"]


@lru_cache()
def get_ai_provider() -> AIProvider:
    """
    Get singleton Claude provider instance.

    Uses LRU cache to ensure only one provider instance is created.
    Future enhancement: Support multiple providers based on config.

    Returns:
        AIProvider: Claude provider instance

    Note:
        Currently returns ClaudeProvider. In the future, this could
        be extended to support multiple providers:
        - Claude (current)
        - LM Studio
        - OpenRouter
        - OpenAI
    """
    settings = get_settings()
    return ClaudeProvider(api_key=settings.anthropic_api_key, enable_cache=True)

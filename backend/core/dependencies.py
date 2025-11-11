"""
Dependency injection functions for FastAPI.

Provides reusable dependencies for database connections, settings,
and AI providers.
"""

from typing import Optional

from backend.config import get_settings, Settings
from backend.database import get_db
from backend.ai_providers.base import AIProvider


# Re-export for convenience
__all__ = ["get_db", "get_settings", "get_ai_provider"]


def get_ai_provider() -> AIProvider:
    """
    Get AI provider instance.

    Placeholder for actual provider instantiation. Will be implemented
    by the Claude Provider subagent to return a ClaudeProvider instance.

    Returns:
        AIProvider: AI provider instance

    Raises:
        NotImplementedError: Until Claude provider is implemented

    Note:
        This will be updated to instantiate the appropriate provider
        based on configuration (Claude, LM Studio, etc.)
    """
    # TODO: Implement when Claude provider is ready
    # Example future implementation:
    #   settings = get_settings()
    #   if settings.ai_provider == 'claude':
    #       return ClaudeProvider(api_key=settings.claude_api_key)
    #   elif settings.ai_provider == 'lmstudio':
    #       return LMStudioProvider(base_url=settings.lmstudio_url)
    raise NotImplementedError("AI provider not yet implemented")

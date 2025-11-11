"""
Dependency injection functions for FastAPI.

Provides reusable dependencies for database connections, settings,
and AI providers.
"""

from typing import Optional

from backend.config import get_settings, Settings
from backend.database import get_db


# Re-export for convenience
__all__ = ["get_db", "get_settings", "get_ai_provider"]


def get_ai_provider():
    """
    Get AI provider instance.

    Placeholder for future AI provider dependency injection.
    Will be implemented in the AI Provider Abstraction subagent.

    Returns:
        None (placeholder)
    """
    # TODO: Implement in AI Provider Abstraction phase
    return None

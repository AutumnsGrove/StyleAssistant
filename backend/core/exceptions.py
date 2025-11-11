"""
Custom exception hierarchy for Style Assistant.

Provides domain-specific exceptions with HTTP status codes for
consistent error handling throughout the application.
"""

from typing import Optional, Dict, Any


class StyleAssistantException(Exception):
    """
    Base exception for all custom exceptions.

    All custom exceptions should inherit from this class to enable
    centralized error handling in middleware.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class DatabaseError(StyleAssistantException):
    """Database operation failed."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)


class AIProviderError(StyleAssistantException):
    """AI provider API error."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status_code, detail=detail)


class ValidationError(StyleAssistantException):
    """Request validation failed."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, detail=detail)


class NotFoundError(StyleAssistantException):
    """Resource not found."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, detail=detail)


class AuthenticationError(StyleAssistantException):
    """Authentication failed."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, detail=detail)

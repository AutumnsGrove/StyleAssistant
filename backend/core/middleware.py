"""
Error handling middleware for consistent error responses.

Catches all exceptions and returns standardized JSON error responses
with proper logging.
"""

import logging
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse

from backend.core.exceptions import GroveAssistantException


logger = logging.getLogger(__name__)


async def error_handling_middleware(request: Request, call_next):
    """
    Global error handler middleware.

    Catches all exceptions and returns standardized error responses.
    Logs errors with context for debugging.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain

    Returns:
        JSONResponse with error details
    """
    try:
        response = await call_next(request)
        return response

    except GroveAssistantException as e:
        # Log custom exceptions
        logger.error(
            f"{e.__class__.__name__}: {e.message}",
            extra={"detail": e.detail, "path": request.url.path},
        )

        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.__class__.__name__,
                "message": e.message,
                "detail": e.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        # Log unexpected exceptions with full traceback
        logger.exception(
            f"Unhandled exception: {str(e)}", extra={"path": request.url.path}
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

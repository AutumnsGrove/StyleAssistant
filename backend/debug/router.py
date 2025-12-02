"""
FastAPI router for debug logging endpoints.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import aiosqlite

from backend.debug.models import DebugLogCreate, DebugLogEntry, DebugLogListResponse
from backend.debug.service import DebugService
from backend.core.dependencies import get_db

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.post("/log", response_model=DebugLogEntry)
async def create_log(
    log_data: DebugLogCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Create a new debug log entry.

    Used by the extension to report errors and important events.

    Args:
        log_data: Log entry data

    Returns:
        DebugLogEntry: Created log entry

    Example:
        POST /api/debug/log
        {
            "level": "error",
            "component": "content_script",
            "message": "Failed to extract product data",
            "stack_trace": "Error: ..."
        }
    """
    debug_service = DebugService(db)
    result = await debug_service.create(
        level=log_data.level,
        message=log_data.message,
        component=log_data.component,
        stack_trace=log_data.stack_trace,
    )
    return result


@router.get("/logs", response_model=DebugLogListResponse)
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by level (info, warning, error)"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(100, ge=1, le=500, description="Maximum logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Get debug logs with optional filtering.

    Returns logs in reverse chronological order (newest first).

    Args:
        level: Filter by log level
        component: Filter by component
        limit: Maximum number of logs
        offset: Pagination offset

    Returns:
        DebugLogListResponse: List of logs with pagination info

    Example:
        GET /api/debug/logs?level=error&limit=50
    """
    debug_service = DebugService(db)
    result = await debug_service.get_logs(
        level=level,
        component=component,
        limit=limit,
        offset=offset,
    )
    return result


@router.delete("/logs")
async def clear_logs(
    older_than_days: Optional[int] = Query(
        None, ge=1, description="Only clear logs older than this many days"
    ),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Clear debug logs.

    Can optionally only clear logs older than a specified number of days.

    Args:
        older_than_days: Only clear logs older than this (optional)

    Returns:
        dict: Number of deleted logs

    Example:
        DELETE /api/debug/logs?older_than_days=7
    """
    debug_service = DebugService(db)
    deleted = await debug_service.clear_logs(older_than_days)
    return {"deleted": deleted, "message": f"Deleted {deleted} log entries"}

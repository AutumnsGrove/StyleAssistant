"""
FastAPI router for cost tracking endpoints.

Provides HTTP endpoints for querying session and total costs.
"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from backend.costs.service import CostTracker
from backend.costs.models import SessionCostResponse, TotalCostResponse
from backend.core.dependencies import get_db

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("/session/{session_id}", response_model=SessionCostResponse)
async def get_session_costs(
    session_id: str, db: aiosqlite.Connection = Depends(get_db)
):
    """
    Get cost breakdown for a specific session.

    Args:
        session_id: UUID of the session to query

    Returns:
        SessionCostResponse with cost breakdown by type, model, and savings

    Example:
        GET /api/costs/session/123e4567-e89b-12d3-a456-426614174000

        Response:
        {
            "total": 0.045,
            "by_type": {"full": 0.030, "basic": 0.015},
            "by_model": {"claude-sonnet-4.5": 0.030, "claude-haiku-4.5": 0.015},
            "request_count": 5,
            "cached_savings": 0.012
        }
    """
    tracker = CostTracker(db)
    return await tracker.get_session_costs(session_id)


@router.get("/total", response_model=TotalCostResponse)
async def get_total_costs(db: aiosqlite.Connection = Depends(get_db)):
    """
    Get all-time cost totals across all sessions.

    Returns:
        TotalCostResponse with aggregate statistics

    Example:
        GET /api/costs/total

        Response:
        {
            "total": 45.67,
            "total_requests": 1234,
            "total_tokens": 5678901,
            "average_cost_per_request": 0.037
        }
    """
    tracker = CostTracker(db)
    return await tracker.get_total_costs()

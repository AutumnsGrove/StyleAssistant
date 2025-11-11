"""
Cost tracking service for logging and aggregating API usage costs.

Handles:
- Logging individual API calls with token counts and costs
- Session-based cost aggregation
- All-time cost totals
- Cached token savings calculations
"""

import aiosqlite
from typing import Dict, Any
import uuid


class CostTracker:
    """Service for tracking and aggregating API costs."""

    def __init__(self, db: aiosqlite.Connection):
        """
        Initialize cost tracker with database connection.

        Args:
            db: Async SQLite database connection
        """
        self.db = db

    async def log_cost(
        self,
        session_id: str,
        model: str,
        tokens_prompt: int,
        tokens_completion: int,
        cost_usd: float,
        tokens_cache_read: int = 0,
        tokens_cache_write: int = 0,
        request_type: str = "analysis",
    ):
        """
        Log API cost to database.

        Args:
            session_id: UUID for current session
            model: Model name (e.g. 'claude-sonnet-4.5-20250929')
            tokens_prompt: Non-cached input tokens
            tokens_completion: Output tokens
            cost_usd: Total cost in USD
            tokens_cache_read: Cached input tokens read
            tokens_cache_write: Cached input tokens written
            request_type: 'analysis', 'full', or 'basic'
        """
        await self.db.execute(
            """
            INSERT INTO cost_log
            (session_id, model, tokens_prompt, tokens_completion, cost_usd,
             tokens_cache_read, tokens_cache_write, request_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                model,
                tokens_prompt,
                tokens_completion,
                cost_usd,
                tokens_cache_read,
                tokens_cache_write,
                request_type,
            ),
        )
        await self.db.commit()

    async def get_session_costs(self, session_id: str) -> Dict[str, Any]:
        """
        Get cost breakdown for a session.

        Args:
            session_id: Session UUID to query

        Returns:
            Dictionary with structure:
            {
                "total": float,
                "by_type": {"analysis": float, "basic": float, ...},
                "by_model": {"sonnet-4.5": float, "haiku-4.5": float},
                "request_count": int,
                "cached_savings": float
            }
        """
        # Get all costs for session
        cursor = await self.db.execute(
            """
            SELECT model, request_type, cost_usd, tokens_cache_read
            FROM cost_log
            WHERE session_id = ?
            """,
            (session_id,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return {
                "total": 0.0,
                "by_type": {},
                "by_model": {},
                "request_count": 0,
                "cached_savings": 0.0,
            }

        total = 0.0
        by_type = {}
        by_model = {}
        cached_savings = 0.0

        for model, request_type, cost, cached_tokens in rows:
            total += cost
            by_type[request_type] = by_type.get(request_type, 0.0) + cost
            by_model[model] = by_model.get(model, 0.0) + cost

            # Calculate savings (cached tokens would have cost 10x more)
            # Cache read = 10% of regular price
            if cached_tokens > 0:
                # Approximate savings: cached_tokens * 0.9 * avg_price_per_token
                # For Sonnet: $3/M = $0.003/1K
                # For Haiku: $0.25/M = $0.00025/1K
                if "sonnet" in model.lower():
                    avg_price = 0.003  # $3 per 1M tokens
                elif "haiku" in model.lower():
                    avg_price = 0.00025  # $0.25 per 1M tokens
                else:
                    avg_price = 0.001  # Default fallback

                savings = (cached_tokens / 1000) * avg_price * 0.9
                cached_savings += savings

        return {
            "total": round(total, 6),
            "by_type": {k: round(v, 6) for k, v in by_type.items()},
            "by_model": {k: round(v, 6) for k, v in by_model.items()},
            "request_count": len(rows),
            "cached_savings": round(cached_savings, 6),
        }

    async def get_total_costs(self) -> Dict[str, Any]:
        """
        Get all-time cost totals.

        Returns:
            Dictionary with structure:
            {
                "total": float,
                "total_requests": int,
                "total_tokens": int,
                "average_cost_per_request": float
            }
        """
        cursor = await self.db.execute(
            """
            SELECT
                SUM(cost_usd) as total_cost,
                COUNT(*) as total_requests,
                SUM(tokens_prompt + tokens_completion) as total_tokens
            FROM cost_log
            """
        )
        row = await cursor.fetchone()

        total_cost = row[0] or 0.0
        total_requests = row[1] or 0
        total_tokens = row[2] or 0

        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0

        return {
            "total": round(total_cost, 6),
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "average_cost_per_request": round(avg_cost, 6),
        }


def generate_session_id() -> str:
    """
    Generate a new session UUID.

    Returns:
        str: UUID4 string for session tracking
    """
    return str(uuid.uuid4())

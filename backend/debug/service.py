"""
Debug logging service for storing and retrieving debug logs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import aiosqlite


class DebugService:
    """Service for managing debug logs in the database."""

    # Maximum logs to keep (auto-cleanup older entries)
    MAX_LOGS = 1000

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(
        self,
        level: str,
        message: str,
        component: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new debug log entry.

        Args:
            level: Log level (info, warning, error)
            message: Log message
            component: Component that generated the log
            stack_trace: Error stack trace if applicable

        Returns:
            dict: Created log entry
        """
        cursor = await self.db.execute(
            """
            INSERT INTO debug_log (level, component, message, stack_trace)
            VALUES (?, ?, ?, ?)
            """,
            (level, component, message, stack_trace),
        )
        await self.db.commit()

        log_id = cursor.lastrowid

        # Auto-cleanup old logs
        await self._cleanup_old_logs()

        return {
            "id": log_id,
            "level": level,
            "component": component,
            "message": message,
            "stack_trace": stack_trace,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_logs(
        self,
        level: Optional[str] = None,
        component: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get debug logs with optional filtering.

        Args:
            level: Filter by log level
            component: Filter by component
            limit: Maximum number of logs to return
            offset: Offset for pagination

        Returns:
            dict: Logs list with pagination info
        """
        # Build query
        conditions = []
        params: List[Any] = []

        if level:
            conditions.append("level = ?")
            params.append(level)

        if component:
            conditions.append("component = ?")
            params.append(component)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = await self.db.execute(
            f"SELECT COUNT(*) FROM debug_log {where_clause}",
            params,
        )
        total = (await count_cursor.fetchone())[0]

        # Get logs
        query = f"""
            SELECT id, level, component, message, stack_trace, timestamp
            FROM debug_log
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()

        logs = [
            {
                "id": row[0],
                "level": row[1],
                "component": row[2],
                "message": row[3],
                "stack_trace": row[4],
                "timestamp": row[5],
            }
            for row in rows
        ]

        return {
            "logs": logs,
            "total": total,
            "has_more": offset + len(logs) < total,
        }

    async def clear_logs(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear debug logs.

        Args:
            older_than_days: Only clear logs older than this many days.
                             If None, clears all logs.

        Returns:
            int: Number of logs deleted
        """
        if older_than_days is not None:
            cursor = await self.db.execute(
                """
                DELETE FROM debug_log
                WHERE timestamp < datetime('now', ? || ' days')
                """,
                (-older_than_days,),
            )
        else:
            cursor = await self.db.execute("DELETE FROM debug_log")

        await self.db.commit()
        return cursor.rowcount

    async def _cleanup_old_logs(self) -> None:
        """Remove oldest logs if over the limit."""
        # Count current logs
        cursor = await self.db.execute("SELECT COUNT(*) FROM debug_log")
        count = (await cursor.fetchone())[0]

        if count > self.MAX_LOGS:
            # Delete oldest logs to get back to limit
            delete_count = count - self.MAX_LOGS
            await self.db.execute(
                """
                DELETE FROM debug_log
                WHERE id IN (
                    SELECT id FROM debug_log
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
                """,
                (delete_count,),
            )
            await self.db.commit()

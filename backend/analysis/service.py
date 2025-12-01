"""
Analysis database service for CRUD operations and cache management.

Handles analysis caching, retrieval, and storage with profile versioning.
"""

import json
from typing import Optional, Dict, Any
import aiosqlite


class AnalysisService:
    """Service for analysis database operations."""

    def __init__(self, db: aiosqlite.Connection):
        """
        Initialize analysis service.

        Args:
            db: Async SQLite database connection
        """
        self.db = db

    async def get_cached(
        self, product_id: int, profile_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis for a product and profile version.

        This is the primary cache lookup method. Returns cached analysis
        if it exists for the exact product + profile version combination.

        Args:
            product_id: Product database ID
            profile_version: Profile version hash (16 chars) or 'basic'

        Returns:
            Analysis dict if cached, None if cache miss
        """
        cursor = await self.db.execute(
            """
            SELECT id, product_id, profile_version, model_used, analysis_type,
                   analysis_data, tokens_input, tokens_output, tokens_cache_read,
                   tokens_cache_write, cost_usd, created_at
            FROM analyses
            WHERE product_id = ? AND profile_version = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (product_id, profile_version),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    async def get_by_product_url(
        self, product_url: str, profile_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis by product URL and profile version.

        Convenience method that joins with products table.

        Args:
            product_url: Product page URL
            profile_version: Profile version hash or 'basic'

        Returns:
            Analysis dict if cached, None otherwise
        """
        cursor = await self.db.execute(
            """
            SELECT a.id, a.product_id, a.profile_version, a.model_used, a.analysis_type,
                   a.analysis_data, a.tokens_input, a.tokens_output, a.tokens_cache_read,
                   a.tokens_cache_write, a.cost_usd, a.created_at
            FROM analyses a
            JOIN products p ON a.product_id = p.id
            WHERE p.product_url = ? AND a.profile_version = ?
            ORDER BY a.created_at DESC
            LIMIT 1
            """,
            (product_url, profile_version),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    async def create(
        self,
        product_id: int,
        profile_version: str,
        model_used: str,
        analysis_type: str,
        analysis_data: Dict[str, Any],
        tokens: Dict[str, int],
        cost_usd: float,
    ) -> int:
        """
        Store a new analysis result.

        Args:
            product_id: Product database ID
            profile_version: Profile version hash or 'basic'
            model_used: AI model identifier
            analysis_type: 'full' or 'basic'
            analysis_data: Analysis result dictionary
            tokens: Token usage dict with input, output, cache_read, cache_write
            cost_usd: Total cost in USD

        Returns:
            Analysis database ID
        """
        analysis_json = json.dumps(analysis_data)

        cursor = await self.db.execute(
            """
            INSERT INTO analyses
            (product_id, profile_version, model_used, analysis_type, analysis_data,
             tokens_input, tokens_output, tokens_cache_read, tokens_cache_write, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                profile_version,
                model_used,
                analysis_type,
                analysis_json,
                tokens.get("input", 0),
                tokens.get("output", 0),
                tokens.get("cache_read", 0),
                tokens.get("cache_write", 0),
                cost_usd,
            ),
        )
        await self.db.commit()

        return cursor.lastrowid

    async def get_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """
        Get analysis by database ID.

        Args:
            analysis_id: Analysis database ID

        Returns:
            Analysis dict if found, None otherwise
        """
        cursor = await self.db.execute(
            """
            SELECT id, product_id, profile_version, model_used, analysis_type,
                   analysis_data, tokens_input, tokens_output, tokens_cache_read,
                   tokens_cache_write, cost_usd, created_at
            FROM analyses
            WHERE id = ?
            """,
            (analysis_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    async def get_product_analyses(self, product_id: int) -> list[Dict[str, Any]]:
        """
        Get all analyses for a product.

        Args:
            product_id: Product database ID

        Returns:
            List of analysis dicts ordered by creation date (newest first)
        """
        cursor = await self.db.execute(
            """
            SELECT id, product_id, profile_version, model_used, analysis_type,
                   analysis_data, tokens_input, tokens_output, tokens_cache_read,
                   tokens_cache_write, cost_usd, created_at
            FROM analyses
            WHERE product_id = ?
            ORDER BY created_at DESC
            """,
            (product_id,),
        )
        rows = await cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    async def delete_for_product(self, product_id: int) -> int:
        """
        Delete all analyses for a product.

        Args:
            product_id: Product database ID

        Returns:
            Number of analyses deleted
        """
        cursor = await self.db.execute(
            "DELETE FROM analyses WHERE product_id = ?",
            (product_id,),
        )
        await self.db.commit()

        return cursor.rowcount

    async def delete_stale(self, profile_version: str) -> int:
        """
        Delete analyses that don't match the current profile version.

        Useful for cleaning up old analyses after profile changes.

        Args:
            profile_version: Current profile version to keep

        Returns:
            Number of analyses deleted
        """
        cursor = await self.db.execute(
            """
            DELETE FROM analyses
            WHERE analysis_type = 'full' AND profile_version != ?
            """,
            (profile_version,),
        )
        await self.db.commit()

        return cursor.rowcount

    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """
        Convert database row to dictionary.

        Args:
            row: Database row

        Returns:
            Analysis dictionary with parsed JSON fields
        """
        result = dict(row)

        # Parse analysis JSON
        if result.get("analysis_data"):
            try:
                result["analysis_data"] = json.loads(result["analysis_data"])
            except json.JSONDecodeError:
                result["analysis_data"] = {}

        return result

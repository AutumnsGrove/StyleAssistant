"""
Product database service for CRUD operations.

Handles product caching, retrieval, and updates in the SQLite database.
"""

import json
from typing import Optional, Dict, Any
import aiosqlite


class ProductService:
    """Service for product database operations."""

    def __init__(self, db: aiosqlite.Connection):
        """
        Initialize product service.

        Args:
            db: Async SQLite database connection
        """
        self.db = db

    async def get_by_url(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get product by URL.

        Args:
            product_url: Product page URL

        Returns:
            Product dict if found, None otherwise
        """
        cursor = await self.db.execute(
            """
            SELECT id, product_url, site, title, price, currency, description,
                   materials, category, colors, sizes, first_seen, last_seen
            FROM products
            WHERE product_url = ?
            """,
            (product_url,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    async def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get product by database ID.

        Args:
            product_id: Product database ID

        Returns:
            Product dict if found, None otherwise
        """
        cursor = await self.db.execute(
            """
            SELECT id, product_url, site, title, price, currency, description,
                   materials, category, colors, sizes, first_seen, last_seen
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    async def create(self, product_data: Dict[str, Any]) -> int:
        """
        Create a new product record.

        Args:
            product_data: Product data dictionary containing:
                - product_url (required)
                - site (required)
                - title, price, currency, description, materials, category
                - colors (list), sizes (list)

        Returns:
            Product database ID
        """
        # Serialize lists to JSON
        colors_json = json.dumps(product_data.get("colors", []))
        sizes_json = json.dumps(product_data.get("sizes", []))

        cursor = await self.db.execute(
            """
            INSERT INTO products
            (product_url, site, title, price, currency, description, materials, category, colors, sizes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_data["product_url"],
                product_data["site"],
                product_data.get("title", ""),
                product_data.get("price", 0.0),
                product_data.get("currency", "USD"),
                product_data.get("description", ""),
                product_data.get("materials", ""),
                product_data.get("category", ""),
                colors_json,
                sizes_json,
            ),
        )
        await self.db.commit()

        return cursor.lastrowid

    async def upsert(self, product_data: Dict[str, Any]) -> int:
        """
        Insert or update product based on URL.

        Updates last_seen timestamp if product exists.

        Args:
            product_data: Product data dictionary

        Returns:
            Product database ID
        """
        existing = await self.get_by_url(product_data.get("product_url", product_data.get("url", "")))

        if existing:
            # Update existing product
            await self._update_product(existing["id"], product_data)
            return existing["id"]
        else:
            # Normalize URL field
            if "url" in product_data and "product_url" not in product_data:
                product_data["product_url"] = product_data["url"]
            return await self.create(product_data)

    async def _update_product(self, product_id: int, product_data: Dict[str, Any]):
        """
        Update existing product record.

        Args:
            product_id: Product database ID
            product_data: Updated product data
        """
        colors_json = json.dumps(product_data.get("colors", []))
        sizes_json = json.dumps(product_data.get("sizes", []))

        await self.db.execute(
            """
            UPDATE products
            SET title = ?, price = ?, currency = ?, description = ?,
                materials = ?, category = ?, colors = ?, sizes = ?,
                last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                product_data.get("title", ""),
                product_data.get("price", 0.0),
                product_data.get("currency", "USD"),
                product_data.get("description", ""),
                product_data.get("materials", ""),
                product_data.get("category", ""),
                colors_json,
                sizes_json,
                product_id,
            ),
        )
        await self.db.commit()

    async def touch(self, product_url: str):
        """
        Update last_seen timestamp for a product.

        Args:
            product_url: Product page URL
        """
        await self.db.execute(
            """
            UPDATE products
            SET last_seen = CURRENT_TIMESTAMP
            WHERE product_url = ?
            """,
            (product_url,),
        )
        await self.db.commit()

    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """
        Convert database row to dictionary.

        Args:
            row: Database row

        Returns:
            Product dictionary with parsed JSON fields
        """
        result = dict(row)

        # Parse JSON lists
        if result.get("colors"):
            try:
                result["colors"] = json.loads(result["colors"])
            except json.JSONDecodeError:
                result["colors"] = []

        if result.get("sizes"):
            try:
                result["sizes"] = json.loads(result["sizes"])
            except json.JSONDecodeError:
                result["sizes"] = []

        return result

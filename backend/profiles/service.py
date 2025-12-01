"""
Profile database service for CRUD operations.

Handles user style profile storage, retrieval, and versioning.
"""

import json
import hashlib
from typing import Optional, Dict, Any
import aiosqlite


class ProfileService:
    """Service for user profile database operations."""

    def __init__(self, db: aiosqlite.Connection):
        """
        Initialize profile service.

        Args:
            db: Async SQLite database connection
        """
        self.db = db

    async def get_current(self) -> Optional[Dict[str, Any]]:
        """
        Get the current user profile.

        Returns:
            Profile dict with version_hash if exists, None otherwise
        """
        cursor = await self.db.execute(
            """
            SELECT id, profile_data, created_at, updated_at
            FROM user_profile
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = await cursor.fetchone()

        if not row:
            return None

        profile_data = json.loads(row["profile_data"])
        version_hash = self._hash_profile(profile_data)

        return {
            "id": row["id"],
            **profile_data,
            "version_hash": version_hash,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def get_version_hash(self) -> Optional[str]:
        """
        Get the current profile's version hash for cache lookups.

        Returns:
            16-character SHA-256 hash if profile exists, None otherwise
        """
        profile = await self.get_current()
        if not profile:
            return None
        return profile["version_hash"]

    async def create(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or replace user profile.

        Only one profile is stored at a time. Creating a new profile
        replaces any existing one.

        Args:
            profile_data: Profile preferences dictionary

        Returns:
            Created profile with version_hash
        """
        # Serialize profile data
        profile_json = json.dumps(profile_data, sort_keys=True)

        # Delete existing profile(s)
        await self.db.execute("DELETE FROM user_profile")

        # Insert new profile
        cursor = await self.db.execute(
            """
            INSERT INTO user_profile (profile_data)
            VALUES (?)
            """,
            (profile_json,),
        )
        await self.db.commit()

        profile_id = cursor.lastrowid

        # Fetch the created profile to get timestamps
        return await self.get_current()

    async def update(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing profile.

        Args:
            profile_data: Updated profile preferences

        Returns:
            Updated profile with new version_hash
        """
        existing = await self.get_current()

        if not existing:
            return await self.create(profile_data)

        profile_json = json.dumps(profile_data, sort_keys=True)

        await self.db.execute(
            """
            UPDATE user_profile
            SET profile_data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (profile_json, existing["id"]),
        )
        await self.db.commit()

        # Fetch updated profile to get timestamps
        return await self.get_current()

    async def delete(self) -> bool:
        """
        Delete user profile.

        Returns:
            True if deleted, False if no profile existed
        """
        cursor = await self.db.execute("DELETE FROM user_profile")
        await self.db.commit()

        return cursor.rowcount > 0

    async def has_profile(self) -> bool:
        """
        Check if a user profile exists.

        Returns:
            True if profile exists, False otherwise
        """
        cursor = await self.db.execute("SELECT 1 FROM user_profile LIMIT 1")
        row = await cursor.fetchone()
        return row is not None

    def _hash_profile(self, profile: Dict[str, Any]) -> str:
        """
        Generate 16-character SHA-256 hash of profile for versioning.

        Used for cache invalidation when profile changes.

        Args:
            profile: Profile dictionary

        Returns:
            16-character hex hash
        """
        # Normalize JSON (sorted keys, no whitespace)
        normalized = json.dumps(profile, sort_keys=True, separators=(",", ":"))

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(normalized.encode("utf-8"))

        # Return first 16 characters (64 bits)
        return hash_obj.hexdigest()[:16]

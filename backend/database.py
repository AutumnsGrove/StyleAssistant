"""
Database connection management and initialization.

Provides async SQLite connection management using aiosqlite with
dependency injection pattern for FastAPI.
"""

import aiosqlite
from pathlib import Path
from typing import AsyncGenerator


DATABASE_PATH = Path("backend/style_assistant.db")


async def init_database():
    """
    Initialize database schema on startup.

    Reads schema from schema.sql and executes it to create all tables
    and indexes. Idempotent - safe to run multiple times.
    """
    # Ensure parent directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema = f.read()

    # Execute schema
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(schema)
        await db.commit()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Dependency for database connections.

    Creates one connection per request with proper cleanup.
    Enables foreign key constraints and row factory for dict-like access.

    Usage:
        @router.get("/items")
        async def get_items(db: aiosqlite.Connection = Depends(get_db)):
            async with db.execute("SELECT * FROM items") as cursor:
                rows = await cursor.fetchall()
                return rows

    Yields:
        aiosqlite.Connection: Database connection with row factory enabled
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db

"""
FastAPI application entry point for GroveAssistant backend.

Configures FastAPI app with CORS, middleware, and routes.
Initializes database on startup.
"""

import logging
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings, Settings
from backend.database import init_database, get_db
from backend.core.middleware import error_handling_middleware
from backend.costs.router import router as costs_router
from backend.analysis.router import router as analysis_router
from backend.profiles.router import router as profiles_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("grove_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Startup:
        - Initialize database schema
        - Log startup information

    Shutdown:
        - Clean up resources (if needed)
    """
    # Startup
    logger.info("Starting GroveAssistant backend...")
    await init_database()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down GroveAssistant backend...")


# Create FastAPI application
app = FastAPI(
    title="GroveAssistant API",
    version="0.1.0",
    description="AI-powered personalized style analysis backend",
    lifespan=lifespan,
)


# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register error handling middleware
app.middleware("http")(error_handling_middleware)


# Register routers
app.include_router(costs_router)
app.include_router(analysis_router)
app.include_router(profiles_router)


@app.get("/health")
async def health_check(db: aiosqlite.Connection = Depends(get_db)):
    """
    Health check endpoint.

    Verifies:
        - API is running
        - Database is accessible
        - Basic connectivity

    Returns:
        dict: Health status and version information
    """
    # Test database connection
    try:
        async with db.execute("SELECT 1") as cursor:
            await cursor.fetchone()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": "0.1.0",
            "error": "Database unavailable",
        }

    return {"status": "ok", "version": "0.1.0"}

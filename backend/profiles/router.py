"""
FastAPI router for user profile endpoints.

Provides HTTP endpoints for managing user style profiles.
"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from backend.profiles.models import ProfileCreate, ProfileResponse, ProfilePreferences
from backend.profiles.service import ProfileService
from backend.core.dependencies import get_db

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(db: aiosqlite.Connection = Depends(get_db)):
    """
    Get current user profile.

    Returns:
        ProfileResponse with profile data and version hash

    Raises:
        HTTPException 404: If no profile exists

    Example:
        GET /api/profile

        Response:
        {
            "id": 1,
            "fit_preferences": ["slim", "regular"],
            "color_palette": ["navy", "gray", "white"],
            "style_goals": ["professional", "minimalist"],
            "body_type": "athletic",
            "priorities": ["comfort", "versatility"],
            "avoidances": ["logos", "bright colors"],
            "version_hash": "a1b2c3d4e5f67890",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }
    """
    profile_service = ProfileService(db)
    profile = await profile_service.get_current()

    if not profile:
        raise HTTPException(status_code=404, detail="No profile found")

    return profile


@router.post("", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate, db: aiosqlite.Connection = Depends(get_db)
):
    """
    Create or replace user profile.

    Creates a new profile, replacing any existing one.
    This triggers cache invalidation for personalized analyses.

    Args:
        profile_data: Profile preferences from style quiz

    Returns:
        ProfileResponse with new profile data and version hash

    Example:
        POST /api/profile
        {
            "fit_preferences": ["slim", "regular"],
            "color_palette": ["navy", "gray", "white"],
            "style_goals": ["professional", "minimalist"],
            "body_type": "athletic",
            "priorities": ["comfort", "versatility"],
            "avoidances": ["logos", "bright colors"]
        }
    """
    profile_service = ProfileService(db)
    profile = await profile_service.create(profile_data.model_dump())

    return profile


@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfilePreferences, db: aiosqlite.Connection = Depends(get_db)
):
    """
    Update existing profile.

    Updates profile with new preferences. Creates if doesn't exist.
    This triggers cache invalidation for personalized analyses.

    Args:
        profile_data: Updated profile preferences

    Returns:
        ProfileResponse with updated profile and new version hash
    """
    profile_service = ProfileService(db)
    profile = await profile_service.update(profile_data.model_dump())

    return profile


@router.delete("")
async def delete_profile(db: aiosqlite.Connection = Depends(get_db)):
    """
    Delete user profile.

    Removes the profile, switching to basic analysis mode.

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException 404: If no profile exists

    Example:
        DELETE /api/profile

        Response:
        {
            "status": "deleted",
            "message": "Profile deleted. Analyses will use basic mode."
        }
    """
    profile_service = ProfileService(db)
    deleted = await profile_service.delete()

    if not deleted:
        raise HTTPException(status_code=404, detail="No profile to delete")

    return {
        "status": "deleted",
        "message": "Profile deleted. Analyses will use basic mode.",
    }


@router.get("/exists")
async def profile_exists(db: aiosqlite.Connection = Depends(get_db)):
    """
    Check if a user profile exists.

    Quick check without returning full profile data.

    Returns:
        dict: Existence status

    Example:
        GET /api/profile/exists

        Response:
        {
            "exists": true
        }
    """
    profile_service = ProfileService(db)
    exists = await profile_service.has_profile()

    return {"exists": exists}

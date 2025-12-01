"""
Pydantic models for user profile-related API requests and responses.

Defines the structure of style profile data with validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProfilePreferences(BaseModel):
    """User style preferences from quiz."""

    fit_preferences: List[str] = Field(
        default_factory=list, description="Preferred fits (e.g., slim, relaxed, oversized)"
    )
    color_palette: List[str] = Field(
        default_factory=list, description="Preferred colors"
    )
    style_goals: List[str] = Field(
        default_factory=list, description="Style objectives (e.g., professional, casual, trendy)"
    )
    body_type: Optional[str] = Field(None, description="Body type description")
    priorities: List[str] = Field(
        default_factory=list, description="What matters most (e.g., comfort, style, durability)"
    )
    avoidances: List[str] = Field(
        default_factory=list, description="What to avoid (e.g., logos, bright colors)"
    )


class ProfileCreate(ProfilePreferences):
    """Profile creation request model."""

    pass


class ProfileResponse(ProfilePreferences):
    """Profile response model with metadata."""

    id: int = Field(..., description="Database ID")
    version_hash: str = Field(..., description="SHA-256 hash for cache invalidation")
    created_at: datetime = Field(..., description="Profile creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        from_attributes = True

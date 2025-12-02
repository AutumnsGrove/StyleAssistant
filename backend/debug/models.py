"""
Pydantic models for debug logging API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class DebugLogCreate(BaseModel):
    """Request model for creating a debug log entry."""

    level: Literal["info", "warning", "error"] = Field(
        ..., description="Log level"
    )
    component: Optional[str] = Field(
        None, description="Component that generated the log (e.g., content_script, popup)"
    )
    message: str = Field(..., description="Log message")
    stack_trace: Optional[str] = Field(None, description="Error stack trace if applicable")


class DebugLogEntry(BaseModel):
    """Response model for a debug log entry."""

    id: int
    level: str
    component: Optional[str]
    message: str
    stack_trace: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class DebugLogListResponse(BaseModel):
    """Response model for listing debug logs."""

    logs: List[DebugLogEntry]
    total: int
    has_more: bool

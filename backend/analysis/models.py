"""
Pydantic models for analysis-related API requests and responses.

Defines the structure of AI analysis data with validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class FitAnalysis(BaseModel):
    """Fit assessment from AI analysis."""

    expected_fit: str = Field(..., description="Description of how it will fit")
    body_type_suitability: str = Field(
        ..., description="How it works with user's body type"
    )
    sizing_notes: str = Field(..., description="Sizing considerations")


class OutfitSuggestion(BaseModel):
    """Single outfit pairing suggestion."""

    occasion: str = Field(..., description="e.g., casual, work, going out")
    pairing: str = Field(..., description="Specific items to pair with")
    styling_tips: str = Field(..., description="How to style this combination")


class AnalysisData(BaseModel):
    """Full AI analysis result structure."""

    style_match_score: int = Field(..., ge=0, le=100, description="Match score 0-100")
    match_reasoning: str = Field(..., description="Explanation of the score")
    fit_analysis: FitAnalysis = Field(..., description="Fit assessment details")
    versatility_score: int = Field(..., ge=0, le=100, description="Versatility score")
    versatility_notes: str = Field(..., description="Versatility explanation")
    outfit_suggestions: List[OutfitSuggestion] = Field(
        ..., description="Outfit pairing suggestions"
    )
    pros: List[str] = Field(..., description="Positive aspects")
    cons: List[str] = Field(..., description="Concerns or limitations")
    overall_recommendation: Literal["buy", "consider", "pass"] = Field(
        ..., description="Final recommendation"
    )
    final_thoughts: str = Field(..., description="Summary and recommendation")


class AnalyzeRequest(BaseModel):
    """Request to analyze a product."""

    url: str = Field(..., description="Product page URL")
    html: Optional[str] = Field(None, description="Page HTML (if available)")
    force_refresh: bool = Field(
        default=False, description="Force new analysis even if cached"
    )


class AnalyzeResponse(BaseModel):
    """Response from product analysis."""

    product_id: int = Field(..., description="Database product ID")
    analysis: Dict[str, Any] = Field(..., description="AI analysis result")
    model_used: str = Field(..., description="AI model used for analysis")
    analysis_type: Literal["full", "basic"] = Field(
        ..., description="Type of analysis performed"
    )
    cost_usd: float = Field(..., description="Cost of this analysis in USD")
    cached: bool = Field(..., description="Whether result was from cache")
    profile_version: Optional[str] = Field(
        None, description="Profile version hash (if personalized)"
    )


class TokenUsage(BaseModel):
    """Token usage breakdown."""

    input: int = Field(..., description="Non-cached input tokens")
    output: int = Field(..., description="Output tokens")
    cache_read: int = Field(default=0, description="Cached input tokens read")
    cache_write: int = Field(default=0, description="Cached input tokens written")


class AnalysisRecord(BaseModel):
    """Database record for analysis."""

    id: int = Field(..., description="Database ID")
    product_id: int = Field(..., description="Product database ID")
    profile_version: str = Field(..., description="Profile version hash")
    model_used: str = Field(..., description="AI model used")
    analysis_type: Literal["full", "basic"] = Field(..., description="Analysis type")
    analysis_data: Dict[str, Any] = Field(..., description="Analysis result")
    tokens_input: int = Field(default=0, description="Input tokens")
    tokens_output: int = Field(default=0, description="Output tokens")
    tokens_cache_read: int = Field(default=0, description="Cached tokens read")
    tokens_cache_write: int = Field(default=0, description="Cached tokens written")
    cost_usd: float = Field(..., description="Cost in USD")
    created_at: datetime = Field(..., description="Analysis timestamp")

    class Config:
        from_attributes = True

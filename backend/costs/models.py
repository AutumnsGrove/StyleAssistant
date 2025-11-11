"""
Pydantic models for cost tracking API responses.

Defines the structure of cost-related API responses with validation.
"""

from pydantic import BaseModel, Field
from typing import Dict


class SessionCostResponse(BaseModel):
    """
    Response for session cost query.

    Contains breakdown of costs by type, model, and savings information
    for a specific session.
    """

    total: float = Field(..., description="Total cost for session in USD")
    by_type: Dict[str, float] = Field(
        ..., description="Cost breakdown by request type (analysis, full, basic)"
    )
    by_model: Dict[str, float] = Field(
        ..., description="Cost breakdown by model (sonnet, haiku)"
    )
    request_count: int = Field(..., description="Total number of requests in session")
    cached_savings: float = Field(
        ..., description="Estimated savings from prompt caching in USD"
    )


class TotalCostResponse(BaseModel):
    """
    Response for all-time cost query.

    Provides aggregate statistics across all sessions and requests.
    """

    total: float = Field(..., description="Total all-time cost in USD")
    total_requests: int = Field(..., description="Total number of API requests")
    total_tokens: int = Field(..., description="Total tokens processed (input+output)")
    average_cost_per_request: float = Field(
        ..., description="Average cost per request in USD"
    )

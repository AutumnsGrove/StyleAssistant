"""
FastAPI router for product analysis endpoints.

Provides HTTP endpoints for analyzing products with AI.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from typing import Optional

from backend.analysis.models import AnalyzeRequest, AnalyzeResponse
from backend.analysis.service import AnalysisService
from backend.products.service import ProductService
from backend.profiles.service import ProfileService
from backend.costs.service import CostTracker, generate_session_id
from backend.extractors.factory import get_extractor, is_supported
from backend.core.dependencies import get_db
from backend.ai_providers.claude import ClaudeProvider
from backend.config import get_settings

logger = logging.getLogger("grove_assistant.analysis")

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_product(
    request: AnalyzeRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Analyze a product and return style recommendations.

    Flow:
    1. Check if URL is from supported site
    2. Extract product data from HTML
    3. Check cache for existing analysis
    4. If cache miss, call AI provider
    5. Store result in database
    6. Return analysis

    Args:
        request: AnalyzeRequest with URL and optional HTML

    Returns:
        AnalyzeResponse with analysis data, cost info, and cache status

    Raises:
        HTTPException 400: If URL is from unsupported site
        HTTPException 422: If product extraction fails
        HTTPException 500: If AI analysis fails
    """
    # Initialize services
    product_service = ProductService(db)
    analysis_service = AnalysisService(db)
    profile_service = ProfileService(db)
    cost_tracker = CostTracker(db)

    # Check URL support
    if not is_supported(request.url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported site. URL must be from a supported retailer.",
        )

    # Get extractor for this URL
    extractor = get_extractor(request.url)
    if not extractor:
        raise HTTPException(status_code=400, detail="No extractor available for URL")

    # Extract product data
    if not request.html:
        raise HTTPException(
            status_code=422,
            detail="HTML content is required for product extraction",
        )

    try:
        product_data = extractor.extract(request.html, request.url)
    except Exception as e:
        logger.error(f"Product extraction failed: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract product data: {str(e)}",
        )

    # Upsert product to database
    product_id = await product_service.upsert(product_data)

    # Get profile version for cache lookup
    profile = await profile_service.get_current()
    profile_version = profile["version_hash"] if profile else "basic"
    analysis_type = "full" if profile else "basic"

    # Check cache (unless force refresh)
    if not request.force_refresh:
        cached = await analysis_service.get_cached(product_id, profile_version)
        if cached:
            logger.info(f"Cache hit for product {product_id}, profile {profile_version}")
            return AnalyzeResponse(
                product_id=product_id,
                analysis=cached["analysis_data"],
                model_used=cached["model_used"],
                analysis_type=cached["analysis_type"],
                cost_usd=0.0,  # No cost for cached result
                cached=True,
                profile_version=profile_version if profile else None,
            )

    # Cache miss - call AI provider
    logger.info(f"Cache miss for product {product_id}, calling AI provider")

    try:
        # Initialize AI provider (lazy load after validations pass)
        settings = get_settings()
        ai_provider = ClaudeProvider(api_key=settings.anthropic_api_key, enable_cache=True)

        # Prepare profile data for AI if exists
        profile_data = None
        if profile:
            profile_data = {
                k: v
                for k, v in profile.items()
                if k not in ("id", "version_hash", "created_at", "updated_at")
            }

        # Call AI provider
        result = await ai_provider.analyze_product(product_data, profile_data)
    except ValueError as e:
        logger.error(f"AI provider configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Please set up API key.",
        )
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}",
        )

    # Store analysis in database
    analysis_id = await analysis_service.create(
        product_id=product_id,
        profile_version=profile_version,
        model_used=result["model_used"],
        analysis_type=analysis_type,
        analysis_data=result["analysis_data"],
        tokens=result["tokens_used"],
        cost_usd=result["cost_usd"],
    )

    # Log cost
    session_id = generate_session_id()
    await cost_tracker.log_cost(
        session_id=session_id,
        model=result["model_used"],
        tokens_prompt=result["tokens_used"]["input"],
        tokens_completion=result["tokens_used"]["output"],
        cost_usd=result["cost_usd"],
        tokens_cache_read=result["tokens_used"].get("cache_read", 0),
        tokens_cache_write=result["tokens_used"].get("cache_write", 0),
        request_type=analysis_type,
    )

    return AnalyzeResponse(
        product_id=product_id,
        analysis=result["analysis_data"],
        model_used=result["model_used"],
        analysis_type=analysis_type,
        cost_usd=result["cost_usd"],
        cached=False,
        profile_version=profile_version if profile else None,
    )


@router.get("/test-connection")
async def test_connection():
    """
    Test connection to AI provider.

    Performs a minimal API call to verify:
    - API key is valid
    - Network connectivity is working
    - Claude API is accessible

    Returns:
        dict: Connection status with provider info

    Example:
        GET /api/test-connection

        Response:
        {
            "status": "ok",
            "provider": "claude",
            "message": "Connection successful"
        }
    """
    try:
        settings = get_settings()
        ai_provider = ClaudeProvider(api_key=settings.anthropic_api_key, enable_cache=True)
        success = await ai_provider.test_connection()

        if success:
            return {
                "status": "ok",
                "provider": "claude",
                "message": "Connection successful",
            }
        else:
            return {
                "status": "error",
                "provider": "claude",
                "message": "Connection test returned false",
            }
    except ValueError as e:
        return {
            "status": "error",
            "provider": "claude",
            "message": "API key not configured",
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "status": "error",
            "provider": "claude",
            "message": str(e),
        }

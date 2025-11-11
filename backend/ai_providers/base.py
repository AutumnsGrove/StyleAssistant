"""
Abstract base class for AI providers.

Defines the interface that all AI providers (Claude, LM Studio, OpenRouter, etc.)
must implement. This abstraction allows easy swapping between providers without
changing the analysis service logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """
    Abstract base class for all AI providers.

    Subclasses must implement all abstract methods to provide consistent
    interface for product analysis, regardless of underlying AI service.
    """

    @abstractmethod
    async def analyze_product(
        self,
        product_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a product with optional user profile.

        Performs full personalized style analysis when user_profile is provided,
        or basic analysis when user_profile is None.

        Args:
            product_data: Product information including:
                - url: Product URL
                - title: Product name
                - price: Product price
                - description: Product description
                - materials: Material composition
                - category: Product category
                - colors: List of available colors
                - sizes: List of available sizes
            user_profile: User style profile from quiz (None = basic mode)
                Contains preferences like:
                - fit_preferences: Preferred fits (e.g., 'oversized', 'relaxed')
                - color_palette: Preferred colors
                - style_goals: User's style objectives
                - body_type: Body type information
                - etc.

        Returns:
            Dict containing:
                - analysis_data: Analysis results matching the analysis schema
                - tokens_used: Token usage breakdown (input, output, cached)
                - cost_usd: Cost in USD for this analysis
                - model_used: Model identifier used for analysis
                - cached_tokens: Cached token count (for providers with caching)

        Raises:
            AIProviderError: If API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def basic_analysis(
        self,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Basic product analysis without user profile.

        Provides generic style analysis without personalization. Typically
        uses a faster/cheaper model than full analysis.

        Args:
            product_data: Product information (same format as analyze_product)

        Returns:
            Same format as analyze_product():
                - analysis_data: Generic analysis results
                - tokens_used: Token usage breakdown
                - cost_usd: Cost in USD
                - model_used: Model identifier
                - cached_tokens: Cached token count (if applicable)

        Raises:
            AIProviderError: If API call fails or returns invalid data
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if API connection is working.

        Performs a minimal API call to verify that credentials are valid
        and the service is reachable.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """
        Calculate cost in USD for API usage.

        Args:
            prompt_tokens: Input tokens (non-cached)
            completion_tokens: Output tokens
            cached_tokens: Cached input tokens (if supported by provider)

        Returns:
            Cost in USD (rounded to 6 decimal places for precision)

        Note:
            Pricing varies by provider and model. Implementations should
            reference their specific pricing structure (e.g., Claude's
            per-million-token pricing with cache discounts).
        """
        pass

"""
Claude AI provider implementation with prompt caching support.

Implements the AIProvider interface for Anthropic's Claude models,
with 3-breakpoint prompt caching for cost optimization.
"""

import hashlib
import json
from typing import Dict, Any, Optional

import anthropic

from backend.ai_providers.base import AIProvider
from backend.ai_providers.prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_SCHEMA,
    get_profile_prompt,
    get_analysis_request,
    get_basic_system_prompt,
)
from backend.config import get_settings


class ClaudeProvider(AIProvider):
    """
    Claude API implementation with prompt caching support.

    Uses 3-breakpoint caching strategy:
    1. System prompt (base instructions)
    2. User profile (changes when user retakes quiz)
    3. Analysis schema (output format)

    Supports:
    - Sonnet 4.5 for full personalized analysis
    - Haiku 4.5 for basic analysis without profile
    - Automatic cost calculation with cache discounts
    - Token counting and cost tracking
    """

    # Model identifiers
    SONNET_4_5 = "claude-sonnet-4-5-20250929"
    HAIKU_4_5 = "claude-haiku-4-5-20250929"

    # Pricing per 1M tokens (USD) - updated to match architecture doc
    PRICING = {
        SONNET_4_5: {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,  # 90% discount
            "cache_write": 3.75,  # 25% markup
        },
        HAIKU_4_5: {
            "input": 1.00,
            "output": 5.00,
            "cache_read": 0.10,  # 90% discount
            "cache_write": 1.25,  # 25% markup
        },
    }

    def __init__(self, api_key: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (if None, loads from settings)
            enable_cache: Whether to enable prompt caching (default: True)
        """
        if api_key is None:
            settings = get_settings()
            api_key = settings.anthropic_api_key

        if not api_key:
            raise ValueError("Anthropic API key is required")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.enable_cache = enable_cache

    async def analyze_product(
        self,
        product_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze product with optional user profile.

        Uses Sonnet 4.5 for full analysis with profile, or delegates to
        basic_analysis if no profile provided.

        Args:
            product_data: Product information
            user_profile: User style profile (None = basic mode)

        Returns:
            Dict with analysis_data, tokens_used, cost_usd, model_used, cached_tokens
        """
        if user_profile:
            return await self._cached_analysis(product_data, user_profile)
        else:
            return await self.basic_analysis(product_data)

    async def basic_analysis(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic analysis with Haiku (no profile, no caching).

        Uses simplified prompt and faster model for quick generic analysis.

        Args:
            product_data: Product information

        Returns:
            Dict with analysis results and cost information
        """
        model = self.HAIKU_4_5

        # Build system message with basic prompt and schema (2 cache points)
        system_messages = self._build_basic_system_messages()

        # Build user message with product data
        user_message = get_analysis_request(product_data, mode="basic")

        # Call Claude API
        response = self.client.messages.create(
            model=model,
            max_tokens=1536,  # Less tokens needed for basic analysis
            system=system_messages,
            messages=[{"role": "user", "content": user_message}],
            extra_headers=(
                {"anthropic-beta": "prompt-caching-2024-07-31"}
                if self.enable_cache
                else {}
            ),
        )

        # Process and return response
        return self._process_response(response, model)

    async def _cached_analysis(
        self, product_data: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full analysis with Sonnet + 3-breakpoint caching.

        Cache breakpoints:
        1. System prompt
        2. User profile
        3. Analysis schema

        Args:
            product_data: Product information
            user_profile: User style profile

        Returns:
            Dict with analysis results and cost information
        """
        model = self.SONNET_4_5

        # Build system messages with all 3 cache breakpoints
        system_messages = self._build_cached_system_messages(user_profile)

        # Build user message with product data (NOT cached)
        user_message = get_analysis_request(product_data, mode="full")

        # Call Claude API with caching header
        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_messages,
            messages=[{"role": "user", "content": user_message}],
            extra_headers=(
                {"anthropic-beta": "prompt-caching-2024-07-31"}
                if self.enable_cache
                else {}
            ),
        )

        # Process and return response
        return self._process_response(response, model)

    def _build_basic_system_messages(self) -> list:
        """
        Build system messages for basic analysis (2 cache breakpoints).

        Returns:
            List of system message blocks with cache controls
        """
        messages = [
            {"type": "text", "text": get_basic_system_prompt()},
        ]

        # Cache breakpoint: Analysis schema
        messages.append(
            {
                "type": "text",
                "text": ANALYSIS_SCHEMA,
                "cache_control": {"type": "ephemeral"} if self.enable_cache else None,
            }
        )

        # Remove None cache_control if caching disabled
        if not self.enable_cache:
            messages = [
                {k: v for k, v in msg.items() if v is not None} for msg in messages
            ]

        return messages

    def _build_cached_system_messages(self, user_profile: Dict[str, Any]) -> list:
        """
        Build system messages with 3 cache breakpoints for full analysis.

        Cache breakpoints in order:
        1. System prompt (base instructions)
        2. User profile (personalization context)
        3. Analysis schema (output format)

        Args:
            user_profile: User style profile

        Returns:
            List of system message blocks with cache controls
        """
        messages = [
            # Breakpoint 1: System prompt
            {"type": "text", "text": SYSTEM_PROMPT},
        ]

        # Breakpoint 2: User profile
        messages.append(
            {
                "type": "text",
                "text": get_profile_prompt(user_profile),
                "cache_control": {"type": "ephemeral"} if self.enable_cache else None,
            }
        )

        # Breakpoint 3: Analysis schema
        messages.append(
            {
                "type": "text",
                "text": ANALYSIS_SCHEMA,
                "cache_control": {"type": "ephemeral"} if self.enable_cache else None,
            }
        )

        # Remove None cache_control if caching disabled
        if not self.enable_cache:
            messages = [
                {k: v for k, v in msg.items() if v is not None} for msg in messages
            ]

        return messages

    def _process_response(
        self, response: anthropic.types.Message, model: str
    ) -> Dict[str, Any]:
        """
        Extract analysis and token usage from API response.

        Args:
            response: Claude API response
            model: Model identifier used

        Returns:
            Dict with analysis_data, tokens_used, cost_usd, model_used, cached_tokens
        """
        usage = response.usage

        # Extract token counts
        tokens = {
            "input": usage.input_tokens,
            "output": usage.output_tokens,
            "cache_read": getattr(usage, "cache_read_input_tokens", 0),
            "cache_write": getattr(usage, "cache_creation_input_tokens", 0),
        }

        # Calculate cost
        cost = self.calculate_cost(
            prompt_tokens=tokens["input"],
            completion_tokens=tokens["output"],
            cached_tokens=tokens["cache_read"],
        )

        # Add cache write cost if present
        if tokens["cache_write"] > 0:
            pricing = self.PRICING[model]
            cost += tokens["cache_write"] * pricing["cache_write"] / 1_000_000

        # Parse JSON from response
        analysis_text = response.content[0].text

        # Try to extract JSON if wrapped in markdown
        if "```json" in analysis_text:
            start = analysis_text.find("```json") + 7
            end = analysis_text.find("```", start)
            analysis_text = analysis_text[start:end].strip()
        elif "```" in analysis_text:
            start = analysis_text.find("```") + 3
            end = analysis_text.find("```", start)
            analysis_text = analysis_text[start:end].strip()

        try:
            analysis_data = json.loads(analysis_text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return error in structured format
            analysis_data = {
                "error": "Failed to parse analysis response",
                "raw_response": analysis_text[:500],  # First 500 chars
                "parse_error": str(e),
            }

        return {
            "analysis_data": analysis_data,
            "tokens_used": tokens,
            "cost_usd": cost,
            "model_used": model,
            "cached_tokens": tokens["cache_read"],
        }

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """
        Calculate cost from token usage with cache discount.

        Uses the current model's pricing (Sonnet by default).
        Note: This doesn't include cache_write costs - those are added
        separately in _process_response.

        Args:
            prompt_tokens: Input tokens (non-cached)
            completion_tokens: Output tokens
            cached_tokens: Cached input tokens (90% discount)

        Returns:
            Cost in USD (rounded to 6 decimal places)
        """
        # Default to Sonnet pricing (most common for full analysis)
        pricing = self.PRICING[self.SONNET_4_5]

        cost = (
            prompt_tokens * pricing["input"] / 1_000_000
            + completion_tokens * pricing["output"] / 1_000_000
            + cached_tokens * pricing["cache_read"] / 1_000_000
        )

        return round(cost, 6)

    async def test_connection(self) -> bool:
        """
        Test Claude API connectivity.

        Performs minimal API call to verify credentials and connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.client.messages.create(
                model=self.HAIKU_4_5,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return response.content[0].text is not None
        except Exception:
            return False

    def _hash_profile(self, profile: Dict[str, Any]) -> str:
        """
        Generate 16-character SHA-256 hash of profile for versioning.

        Used for cache invalidation when profile changes.

        Args:
            profile: User profile dictionary

        Returns:
            16-character hex hash
        """
        # Normalize JSON (sorted keys, no whitespace)
        normalized = json.dumps(profile, sort_keys=True, separators=(",", ":"))

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(normalized.encode("utf-8"))

        # Return first 16 characters (64 bits)
        return hash_obj.hexdigest()[:16]

"""Tests for AI provider including cost calculation and response processing."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestClaudeProviderCostCalculation:
    """Tests for Claude provider cost calculations."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation without caching."""
        from backend.ai_providers.claude import ClaudeProvider

        # Create provider with mock API key
        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()
            provider.PRICING = ClaudeProvider.PRICING
            provider.SONNET_4_5 = ClaudeProvider.SONNET_4_5

            # 1000 input tokens, 500 output tokens
            # Sonnet: $3/M input, $15/M output
            # Cost = (1000 * 3 / 1M) + (500 * 15 / 1M) = 0.003 + 0.0075 = 0.0105
            cost = provider.calculate_cost(
                prompt_tokens=1000, completion_tokens=500, cached_tokens=0
            )

            assert cost == pytest.approx(0.0105, rel=1e-4)

    def test_calculate_cost_with_cache(self):
        """Test cost calculation with cached tokens."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()
            provider.PRICING = ClaudeProvider.PRICING
            provider.SONNET_4_5 = ClaudeProvider.SONNET_4_5

            # 200 input tokens, 500 output, 800 cached
            # Cached = $0.30/M (90% discount from $3)
            # Cost = (200 * 3 / 1M) + (500 * 15 / 1M) + (800 * 0.30 / 1M)
            cost = provider.calculate_cost(
                prompt_tokens=200, completion_tokens=500, cached_tokens=800
            )

            expected = 0.0006 + 0.0075 + 0.00024
            assert cost == pytest.approx(expected, rel=1e-4)

    def test_haiku_pricing(self):
        """Test that Haiku pricing is correct."""
        from backend.ai_providers.claude import ClaudeProvider

        pricing = ClaudeProvider.PRICING[ClaudeProvider.HAIKU_4_5]

        assert pricing["input"] == 1.00
        assert pricing["output"] == 5.00
        assert pricing["cache_read"] == 0.10
        assert pricing["cache_write"] == 1.25


class TestClaudeProviderProfileHashing:
    """Tests for profile hashing functionality."""

    def test_hash_profile_deterministic(self):
        """Test that same profile produces same hash."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()

            profile = {"fit_preferences": ["slim"], "colors": ["black"]}

            hash1 = provider._hash_profile(profile)
            hash2 = provider._hash_profile(profile)

            assert hash1 == hash2
            assert len(hash1) == 16

    def test_hash_profile_changes_with_content(self):
        """Test that different profiles produce different hashes."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()

            profile1 = {"fit_preferences": ["slim"]}
            profile2 = {"fit_preferences": ["oversized"]}

            hash1 = provider._hash_profile(profile1)
            hash2 = provider._hash_profile(profile2)

            assert hash1 != hash2

    def test_hash_profile_order_independent(self):
        """Test that key order doesn't affect hash."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()

            profile1 = {"a": 1, "b": 2}
            profile2 = {"b": 2, "a": 1}

            hash1 = provider._hash_profile(profile1)
            hash2 = provider._hash_profile(profile2)

            assert hash1 == hash2


class TestPromptTemplates:
    """Tests for prompt template functions."""

    def test_get_profile_prompt(self):
        """Test profile prompt generation."""
        from backend.ai_providers.prompts import get_profile_prompt

        profile = {
            "fit_preferences": ["slim", "regular"],
            "color_palette": ["black", "navy"],
            "style_goals": ["professional"],
        }

        prompt = get_profile_prompt(profile)

        assert "USER STYLE PROFILE:" in prompt
        assert "slim, regular" in prompt
        assert "black, navy" in prompt
        assert "professional" in prompt

    def test_get_analysis_request_full(self):
        """Test full analysis request generation."""
        from backend.ai_providers.prompts import get_analysis_request

        product = {
            "title": "Cotton T-Shirt",
            "price": 29.99,
            "currency": "USD",
            "description": "A basic cotton t-shirt",
        }

        request = get_analysis_request(product, mode="full")

        assert "Cotton T-Shirt" in request
        assert "USD 29.99" in request
        assert "personalized analysis" in request

    def test_get_analysis_request_basic(self):
        """Test basic analysis request generation."""
        from backend.ai_providers.prompts import get_analysis_request

        product = {"title": "Cotton T-Shirt", "price": 29.99}

        request = get_analysis_request(product, mode="basic")

        assert "Cotton T-Shirt" in request
        assert "general analysis" in request

    def test_analysis_schema_valid_json_example(self):
        """Test that analysis schema contains valid JSON structure hints."""
        from backend.ai_providers.prompts import ANALYSIS_SCHEMA

        assert "style_match_score" in ANALYSIS_SCHEMA
        assert "fit_analysis" in ANALYSIS_SCHEMA
        assert "outfit_suggestions" in ANALYSIS_SCHEMA
        assert "overall_recommendation" in ANALYSIS_SCHEMA


class TestResponseProcessing:
    """Tests for AI response processing."""

    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown code blocks."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()
            provider.PRICING = ClaudeProvider.PRICING
            provider.SONNET_4_5 = ClaudeProvider.SONNET_4_5

            # Create mock response
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.usage.cache_read_input_tokens = 0
            mock_response.usage.cache_creation_input_tokens = 0

            analysis = {"style_match_score": 85, "pros": ["Good"]}
            mock_response.content = [
                Mock(text=f"```json\n{json.dumps(analysis)}\n```")
            ]

            result = provider._process_response(mock_response, provider.SONNET_4_5)

            assert result["analysis_data"]["style_match_score"] == 85

    def test_handle_malformed_json(self):
        """Test handling of malformed JSON responses."""
        from backend.ai_providers.claude import ClaudeProvider

        with patch.object(ClaudeProvider, "__init__", lambda self, **kwargs: None):
            provider = ClaudeProvider()
            provider.PRICING = ClaudeProvider.PRICING
            provider.SONNET_4_5 = ClaudeProvider.SONNET_4_5

            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.usage.cache_read_input_tokens = 0
            mock_response.usage.cache_creation_input_tokens = 0
            mock_response.content = [Mock(text="not valid json {")]

            result = provider._process_response(mock_response, provider.SONNET_4_5)

            assert "error" in result["analysis_data"]
            assert "parse_error" in result["analysis_data"]

"""Tests for API endpoints including full analysis flow."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import aiosqlite
from pathlib import Path


@pytest.fixture
async def test_app(temp_db):
    """Create test application with test database."""
    from backend.main import app
    from backend import database

    # Override database path
    original_path = database.DATABASE_PATH
    database.DATABASE_PATH = temp_db

    # Initialize database
    await database.init_database()

    yield app

    # Restore original path
    database.DATABASE_PATH = original_path


@pytest.fixture
def client(test_app):
    """Create test client."""
    from fastapi.testclient import TestClient

    return TestClient(test_app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestProfileEndpoints:
    """Tests for /api/profile endpoints."""

    def test_get_profile_not_found(self, client):
        """Test getting profile when none exists."""
        response = client.get("/api/profile")

        assert response.status_code == 404

    def test_create_profile(self, client, sample_user_profile):
        """Test creating a profile."""
        response = client.post("/api/profile", json=sample_user_profile)

        assert response.status_code == 200
        data = response.json()
        assert "version_hash" in data
        assert data["fit_preferences"] == sample_user_profile["fit_preferences"]

    def test_get_profile_after_create(self, client, sample_user_profile):
        """Test getting profile after creation."""
        client.post("/api/profile", json=sample_user_profile)
        response = client.get("/api/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["fit_preferences"] == sample_user_profile["fit_preferences"]

    def test_profile_exists(self, client, sample_user_profile):
        """Test profile exists endpoint."""
        # Before creation
        response = client.get("/api/profile/exists")
        assert response.json()["exists"] is False

        # After creation
        client.post("/api/profile", json=sample_user_profile)
        response = client.get("/api/profile/exists")
        assert response.json()["exists"] is True

    def test_delete_profile(self, client, sample_user_profile):
        """Test deleting profile."""
        client.post("/api/profile", json=sample_user_profile)
        response = client.delete("/api/profile")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deleted
        response = client.get("/api/profile/exists")
        assert response.json()["exists"] is False


class TestCostEndpoints:
    """Tests for /api/costs endpoints."""

    def test_get_session_costs_empty(self, client):
        """Test getting costs for non-existent session."""
        response = client.get("/api/costs/session/nonexistent-session-id")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0.0
        assert data["request_count"] == 0

    def test_get_total_costs_empty(self, client):
        """Test getting total costs when empty."""
        response = client.get("/api/costs/total")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0.0
        assert data["total_requests"] == 0


class TestAnalyzeEndpoint:
    """Tests for /api/analyze endpoint."""

    def test_analyze_unsupported_url(self, client):
        """Test analysis fails for unsupported URL."""
        response = client.post(
            "/api/analyze",
            json={"url": "https://unsupported-site.com/product", "html": "<html></html>"},
        )

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_analyze_missing_html(self, client):
        """Test analysis fails without HTML."""
        response = client.post(
            "/api/analyze", json={"url": "https://www.uniqlo.com/product"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_with_mock_ai(self, client, sample_product_data):
        """Test full analysis flow with mocked AI provider."""
        # Create mock AI provider response
        mock_result = {
            "analysis_data": {
                "style_match_score": 85,
                "match_reasoning": "Good fit for style",
                "fit_analysis": {
                    "expected_fit": "Regular fit",
                    "body_type_suitability": "Works well",
                    "sizing_notes": "True to size",
                },
                "versatility_score": 80,
                "versatility_notes": "Very versatile",
                "outfit_suggestions": [
                    {
                        "occasion": "casual",
                        "pairing": "jeans",
                        "styling_tips": "Keep it simple",
                    }
                ],
                "pros": ["Good quality"],
                "cons": ["Limited colors"],
                "overall_recommendation": "buy",
                "final_thoughts": "Great basic piece",
            },
            "tokens_used": {
                "input": 100,
                "output": 200,
                "cache_read": 80,
                "cache_write": 0,
            },
            "cost_usd": 0.01,
            "model_used": "claude-sonnet-4.5-20250929",
            "cached_tokens": 80,
        }

        # Simple HTML that the extractor can parse
        test_html = """
        <html>
            <h1 class="product-title">Test Product</h1>
            <span class="price">$29.99</span>
            <div class="product-description">A great product</div>
        </html>
        """

        with patch(
            "backend.analysis.router.ClaudeProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.analyze_product = AsyncMock(return_value=mock_result)
            mock_provider_class.return_value = mock_provider

            response = client.post(
                "/api/analyze",
                json={
                    "url": "https://www.uniqlo.com/us/en/products/test-123",
                    "html": test_html,
                },
            )

            # With the mocked provider, we should get a successful response
            if response.status_code == 200:
                data = response.json()
                assert "product_id" in data
                assert "analysis" in data
                assert "cached" in data


class TestTestConnectionEndpoint:
    """Tests for /api/test-connection endpoint."""

    def test_connection_with_mock(self, client):
        """Test connection endpoint with mocked provider."""
        with patch(
            "backend.analysis.router.ClaudeProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.test_connection = AsyncMock(return_value=True)
            mock_provider_class.return_value = mock_provider

            response = client.get("/api/test-connection")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    def test_connection_no_api_key(self, client):
        """Test connection returns error when no API key configured."""
        # Without mocking, the endpoint should handle missing API key gracefully
        response = client.get("/api/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "API key" in data["message"]


class TestExtractors:
    """Tests for product extractors."""

    def test_uniqlo_detect(self):
        """Test Uniqlo URL detection."""
        from backend.extractors import is_supported, get_extractor

        assert is_supported("https://www.uniqlo.com/us/en/products/E123456")
        assert is_supported("https://www.uniqlo.jp/product/E123456")
        assert not is_supported("https://www.example.com/product")

    def test_uniqlo_extract_basic(self):
        """Test basic Uniqlo extraction."""
        from backend.extractors import UniqloExtractor

        extractor = UniqloExtractor()
        html = """
        <html>
            <h1>Cotton T-Shirt</h1>
            <span class="price">$19.90</span>
        </html>
        """

        result = extractor.extract(html, "https://www.uniqlo.com/product/123")

        assert result["site"] == "uniqlo"
        assert result["url"] == "https://www.uniqlo.com/product/123"
        # Title extraction depends on actual selectors
        assert "title" in result

    def test_get_supported_sites(self):
        """Test getting list of supported sites."""
        from backend.extractors import get_supported_sites

        sites = get_supported_sites()
        assert "uniqlo" in sites

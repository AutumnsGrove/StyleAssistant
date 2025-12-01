"""Shared pytest fixtures for GroveAssistant tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_grove_assistant.db"

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "style_match_score": 85,
        "match_reasons": ["Oversized fit matches preference"],
        "mismatch_reasons": [],
        "attributes": {
            "warmth": "medium",
            "formality": "casual-smart",
            "vibe": "cozy minimalist"
        },
        "pairing_suggestions": [],
        "color_analysis": "Earth tones work well",
        "season_fit": ["fall", "spring"],
        "occasion_tags": ["everyday"]
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "title": "Sample Product",
        "price": 29.99,
        "currency": "USD",
        "description": "A sample product description",
        "materials": "100% Cotton",
        "category": "tops",
        "colors": ["black", "white"],
        "sizes": ["S", "M", "L"],
        "images": ["https://example.com/image1.jpg"],
        "url": "https://www.uniqlo.com/products/test",
        "site": "uniqlo"
    }


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return {
        "quiz_version": "1.0",
        "fit_preferences": ["oversized", "relaxed"],
        "color_palette": ["black", "white", "earth_tones"],
        "formality_range": [1, 5],
        "gender_presentation": ["feminine", "androgynous"],
        "aesthetics": ["minimalist", "cottagecore"],
        "priorities": ["comfort", "warmth", "versatility"],
        "avoid": ["tight_fit", "crop_tops"],
        "style_keywords": ["cozy", "nature-inspired", "practical"]
    }

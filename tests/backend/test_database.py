"""Tests for database operations including schema, CRUD, and cache lookup."""

import pytest
import aiosqlite
import json
from pathlib import Path


@pytest.fixture
async def test_db(temp_db):
    """Create and initialize a test database."""
    # Read schema
    schema_path = Path(__file__).parent.parent.parent / "backend" / "schema.sql"
    with open(schema_path) as f:
        schema = f.read()

    # Initialize database
    async with aiosqlite.connect(temp_db) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(schema)
        await db.commit()
        yield db


class TestSchemaCreation:
    """Tests for database schema creation."""

    async def test_tables_exist(self, test_db):
        """Test that all expected tables are created."""
        expected_tables = [
            "user_profile",
            "products",
            "analyses",
            "settings",
            "cost_log",
            "debug_log",
        ]

        cursor = await test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    async def test_indexes_exist(self, test_db):
        """Test that performance indexes are created."""
        expected_indexes = [
            "idx_products_url",
            "idx_analyses_lookup",
            "idx_cost_log_session",
        ]

        cursor = await test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in await cursor.fetchall()]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not found"


class TestProductService:
    """Tests for ProductService CRUD operations."""

    async def test_create_product(self, test_db, sample_product_data):
        """Test creating a new product."""
        from backend.products.service import ProductService

        service = ProductService(test_db)
        product_data = {
            "product_url": sample_product_data["url"],
            "site": sample_product_data["site"],
            "title": sample_product_data["title"],
            "price": sample_product_data["price"],
            "currency": sample_product_data["currency"],
            "colors": sample_product_data["colors"],
            "sizes": sample_product_data["sizes"],
        }

        product_id = await service.create(product_data)

        assert product_id is not None
        assert product_id > 0

    async def test_get_by_url(self, test_db, sample_product_data):
        """Test retrieving product by URL."""
        from backend.products.service import ProductService

        service = ProductService(test_db)
        product_data = {
            "product_url": sample_product_data["url"],
            "site": sample_product_data["site"],
            "title": sample_product_data["title"],
            "price": sample_product_data["price"],
        }

        await service.create(product_data)
        product = await service.get_by_url(sample_product_data["url"])

        assert product is not None
        assert product["title"] == sample_product_data["title"]
        assert product["price"] == sample_product_data["price"]

    async def test_get_by_url_not_found(self, test_db):
        """Test that non-existent URL returns None."""
        from backend.products.service import ProductService

        service = ProductService(test_db)
        product = await service.get_by_url("https://example.com/nonexistent")

        assert product is None

    async def test_upsert_creates_new(self, test_db, sample_product_data):
        """Test that upsert creates new product if not exists."""
        from backend.products.service import ProductService

        service = ProductService(test_db)
        product_id = await service.upsert(sample_product_data)

        assert product_id is not None
        product = await service.get_by_id(product_id)
        assert product["title"] == sample_product_data["title"]

    async def test_upsert_updates_existing(self, test_db, sample_product_data):
        """Test that upsert updates existing product."""
        from backend.products.service import ProductService

        service = ProductService(test_db)

        # Create first
        product_id = await service.upsert(sample_product_data)

        # Update with new price
        updated_data = sample_product_data.copy()
        updated_data["price"] = 39.99
        updated_id = await service.upsert(updated_data)

        assert updated_id == product_id
        product = await service.get_by_id(product_id)
        assert product["price"] == 39.99


class TestProfileService:
    """Tests for ProfileService CRUD operations."""

    async def test_create_profile(self, test_db, sample_user_profile):
        """Test creating a user profile."""
        from backend.profiles.service import ProfileService

        service = ProfileService(test_db)
        profile = await service.create(sample_user_profile)

        assert profile is not None
        assert profile["id"] > 0
        assert "version_hash" in profile
        assert len(profile["version_hash"]) == 16

    async def test_get_current_profile(self, test_db, sample_user_profile):
        """Test retrieving current profile."""
        from backend.profiles.service import ProfileService

        service = ProfileService(test_db)
        await service.create(sample_user_profile)
        profile = await service.get_current()

        assert profile is not None
        assert profile["fit_preferences"] == sample_user_profile["fit_preferences"]

    async def test_profile_version_hash_changes(self, test_db, sample_user_profile):
        """Test that version hash changes when profile changes."""
        from backend.profiles.service import ProfileService

        service = ProfileService(test_db)
        profile1 = await service.create(sample_user_profile)
        hash1 = profile1["version_hash"]

        # Update profile
        updated_profile = sample_user_profile.copy()
        updated_profile["fit_preferences"] = ["slim"]
        profile2 = await service.update(updated_profile)
        hash2 = profile2["version_hash"]

        assert hash1 != hash2

    async def test_has_profile(self, test_db, sample_user_profile):
        """Test checking profile existence."""
        from backend.profiles.service import ProfileService

        service = ProfileService(test_db)

        assert await service.has_profile() is False

        await service.create(sample_user_profile)

        assert await service.has_profile() is True

    async def test_delete_profile(self, test_db, sample_user_profile):
        """Test deleting profile."""
        from backend.profiles.service import ProfileService

        service = ProfileService(test_db)
        await service.create(sample_user_profile)

        deleted = await service.delete()
        assert deleted is True
        assert await service.has_profile() is False


class TestAnalysisService:
    """Tests for AnalysisService with cache lookup."""

    async def test_create_and_cache_lookup(self, test_db, sample_product_data):
        """Test creating analysis and retrieving from cache."""
        from backend.products.service import ProductService
        from backend.analysis.service import AnalysisService

        product_service = ProductService(test_db)
        analysis_service = AnalysisService(test_db)

        # Create product first
        product_id = await product_service.upsert(sample_product_data)

        # Create analysis
        analysis_data = {
            "style_match_score": 85,
            "match_reasoning": "Good fit",
            "pros": ["Nice color"],
            "cons": [],
        }
        tokens = {"input": 100, "output": 50, "cache_read": 80, "cache_write": 0}

        analysis_id = await analysis_service.create(
            product_id=product_id,
            profile_version="abc123def456789",
            model_used="claude-sonnet-4.5-20250929",
            analysis_type="full",
            analysis_data=analysis_data,
            tokens=tokens,
            cost_usd=0.01,
        )

        assert analysis_id > 0

        # Cache lookup
        cached = await analysis_service.get_cached(product_id, "abc123def456789")
        assert cached is not None
        assert cached["analysis_data"]["style_match_score"] == 85

    async def test_cache_miss_different_profile(self, test_db, sample_product_data):
        """Test that different profile version results in cache miss."""
        from backend.products.service import ProductService
        from backend.analysis.service import AnalysisService

        product_service = ProductService(test_db)
        analysis_service = AnalysisService(test_db)

        product_id = await product_service.upsert(sample_product_data)

        # Create analysis with one profile version
        await analysis_service.create(
            product_id=product_id,
            profile_version="version1",
            model_used="claude-sonnet-4.5-20250929",
            analysis_type="full",
            analysis_data={"score": 85},
            tokens={"input": 100, "output": 50},
            cost_usd=0.01,
        )

        # Look up with different version
        cached = await analysis_service.get_cached(product_id, "version2")
        assert cached is None

    async def test_basic_analysis_cache(self, test_db, sample_product_data):
        """Test caching for basic analysis (no profile)."""
        from backend.products.service import ProductService
        from backend.analysis.service import AnalysisService

        product_service = ProductService(test_db)
        analysis_service = AnalysisService(test_db)

        product_id = await product_service.upsert(sample_product_data)

        # Create basic analysis
        await analysis_service.create(
            product_id=product_id,
            profile_version="basic",
            model_used="claude-haiku-4.5-20250929",
            analysis_type="basic",
            analysis_data={"score": 70},
            tokens={"input": 50, "output": 25},
            cost_usd=0.005,
        )

        # Verify cache lookup works for basic
        cached = await analysis_service.get_cached(product_id, "basic")
        assert cached is not None
        assert cached["analysis_type"] == "basic"


class TestCostTracker:
    """Tests for CostTracker service."""

    async def test_log_and_retrieve_session_costs(self, test_db):
        """Test logging and retrieving session costs."""
        from backend.costs.service import CostTracker, generate_session_id

        tracker = CostTracker(test_db)
        session_id = generate_session_id()

        # Log some costs
        await tracker.log_cost(
            session_id=session_id,
            model="claude-sonnet-4.5-20250929",
            tokens_prompt=100,
            tokens_completion=50,
            cost_usd=0.01,
            tokens_cache_read=80,
            request_type="full",
        )

        await tracker.log_cost(
            session_id=session_id,
            model="claude-haiku-4.5-20250929",
            tokens_prompt=50,
            tokens_completion=25,
            cost_usd=0.005,
            request_type="basic",
        )

        # Retrieve session costs
        costs = await tracker.get_session_costs(session_id)

        assert costs["total"] == 0.015
        assert costs["request_count"] == 2
        assert "claude-sonnet-4.5-20250929" in costs["by_model"]
        assert "full" in costs["by_type"]

    async def test_total_costs(self, test_db):
        """Test retrieving total costs."""
        from backend.costs.service import CostTracker, generate_session_id

        tracker = CostTracker(test_db)

        # Log costs in different sessions
        for _ in range(3):
            await tracker.log_cost(
                session_id=generate_session_id(),
                model="claude-sonnet-4.5-20250929",
                tokens_prompt=100,
                tokens_completion=50,
                cost_usd=0.01,
                request_type="full",
            )

        totals = await tracker.get_total_costs()

        assert totals["total_requests"] == 3
        assert totals["total"] == 0.03

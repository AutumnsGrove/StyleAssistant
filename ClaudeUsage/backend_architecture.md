# Backend Architecture Plan

**Project**: Style Assistant Browser Extension
**Phase**: Architecture Validation
**Date**: 2025-11-11
**Status**: Finalized - Ready for Implementation

---

## Executive Summary

This document provides the final validated architecture for the Style Assistant backend. After reviewing the project specification and technical research findings, this architecture balances the spec's simplicity with the research's best practices, optimizing for a small-scale local MVP while maintaining extensibility for future enhancements.

**Key Architecture Decisions**:
1. **Hybrid directory structure** - Domain-driven for domains, type-based for utilities
2. **aiosqlite with dependency injection** - Non-blocking async operations
3. **4-breakpoint prompt caching** - System, profile, schema, product context
4. **Service layer pattern** - Thin routers, business logic in services
5. **SHA-256 profile versioning** - 16-character hash for cache invalidation
6. **Base class AI provider abstraction** - Supports future provider swapping
7. **Middleware-based error handling** - Consistent error responses with logging

**Expected Performance**:
- **Cost reduction**: 50-70% savings via prompt caching after initial requests
- **Response time**: <2s for cached profile analysis, <3s for initial analysis
- **Concurrency**: Handles 10-20 concurrent requests without blocking

---

## 1. Directory Structure

### Final Decision: Hybrid Approach

After evaluating both the spec's type-based structure and the research's domain-driven recommendation, I'm choosing a **hybrid approach** that combines the best of both:

**Rationale**:
- The spec suggests 4 clear domains: analysis, products, profiles, costs
- Research recommends domain-driven for better locality and scalability
- AI provider abstraction is cross-cutting and deserves its own module
- Utilities (image processing, hashing) are shared and don't fit domain boundaries

### Directory Layout

```
backend/
├── main.py                     # FastAPI app initialization, middleware, CORS
├── config.py                   # Settings, environment variables, constants
├── database.py                 # Database connection, schema initialization
│
├── core/                       # Cross-cutting concerns
│   ├── __init__.py
│   ├── dependencies.py         # Global dependencies (db, settings, auth)
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── middleware.py           # Error handling, logging middleware
│   └── security.py             # API key validation (future)
│
├── ai_providers/               # AI provider abstraction layer
│   ├── __init__.py
│   ├── base.py                 # Abstract AIProvider base class
│   ├── claude.py               # ClaudeProvider implementation
│   ├── schemas.py              # Common AI request/response models
│   ├── cost_calculator.py      # Token cost calculation utilities
│   └── prompts.py              # Prompt templates and caching logic
│
├── analysis/                   # Analysis domain
│   ├── __init__.py
│   ├── router.py               # POST /api/v1/analyze
│   ├── models.py               # DB models (analyses table)
│   ├── schemas.py              # Pydantic request/response models
│   ├── service.py              # AnalysisService - business logic
│   └── cache.py                # Cache lookup and storage logic
│
├── products/                   # Product domain
│   ├── __init__.py
│   ├── models.py               # DB models (products table)
│   ├── schemas.py              # Product schemas
│   ├── service.py              # ProductService - storage/retrieval
│   └── extractors/             # Site-specific extractors
│       ├── __init__.py
│       ├── base.py             # BaseExtractor abstract class
│       └── uniqlo.py           # UniqloExtractor (MVP)
│
├── profiles/                   # User profile domain
│   ├── __init__.py
│   ├── models.py               # DB models (user_profile table)
│   ├── schemas.py              # Profile schemas
│   ├── service.py              # ProfileService
│   └── versioning.py           # Profile hash generation
│
├── costs/                      # Cost tracking domain
│   ├── __init__.py
│   ├── router.py               # GET /api/v1/costs/...
│   ├── models.py               # DB models (cost_log table)
│   ├── schemas.py              # Cost schemas
│   └── service.py              # CostService - aggregation, tracking
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── image_processing.py     # WebP conversion, compression
    └── logging_utils.py        # Structured logging helpers
```

**Why This Structure?**

✅ **Domain cohesion**: Related code grouped together (analysis/, products/)
✅ **Clear boundaries**: Each domain has its own models, schemas, services
✅ **Shared utilities**: Cross-cutting concerns in core/ and utils/
✅ **Easy navigation**: Developer knows exactly where to find code
✅ **Testable**: Each service can be tested independently
✅ **Scalable**: Easy to add new domains or providers

**Trade-offs**:
- Slightly more directories than pure type-based (8 vs 4)
- Requires understanding of domain boundaries
- Some duplication of file names (models.py, schemas.py)

**Verdict**: The benefits outweigh the costs for this project size.

---

## 2. Database Architecture

### Schema Design

The spec's schema is solid. I'm adding **indexes** and **constraints** for performance and data integrity.

#### Enhanced Schema

```sql
-- User style profile
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    profile_data TEXT NOT NULL,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product cache
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_url TEXT UNIQUE NOT NULL,
    site TEXT NOT NULL CHECK(site IN ('uniqlo')),  -- Constraint for valid sites
    title TEXT,
    price REAL CHECK(price >= 0),  -- Non-negative price
    currency TEXT DEFAULT 'USD',
    description TEXT,
    materials TEXT,
    category TEXT,
    colors TEXT,  -- JSON array
    sizes TEXT,   -- JSON array
    image_data BLOB,  -- Store WebP images directly (MVP approach)
    raw_data TEXT,  -- JSON blob of full extracted data
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis cache
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    profile_version TEXT NOT NULL,  -- SHA-256 hash (16 chars)
    model_used TEXT NOT NULL CHECK(model_used IN (
        'claude-sonnet-4.5-20250929',
        'claude-haiku-4.5-20250929'
    )),
    analysis_type TEXT NOT NULL CHECK(analysis_type IN ('full', 'basic')),
    analysis_data TEXT NOT NULL,  -- JSON blob
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    tokens_cache_read INTEGER DEFAULT 0,
    tokens_cache_write INTEGER DEFAULT 0,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON for complex settings
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost tracking log
CREATE TABLE cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,  -- UUID for current session
    model TEXT NOT NULL,
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    tokens_cache_read INTEGER DEFAULT 0,
    tokens_cache_write INTEGER DEFAULT 0,
    cost_usd REAL NOT NULL,
    request_type TEXT CHECK(request_type IN ('analysis', 'full', 'basic')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Debug log
CREATE TABLE debug_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK(level IN ('info', 'warning', 'error')),
    component TEXT,
    message TEXT NOT NULL,
    stack_trace TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_products_url ON products(product_url);
CREATE INDEX idx_products_site ON products(site, last_seen);

CREATE INDEX idx_analyses_lookup ON analyses(product_id, profile_version);
CREATE INDEX idx_analyses_product ON analyses(product_id);
CREATE INDEX idx_analyses_created ON analyses(created_at);

CREATE INDEX idx_cost_log_session ON cost_log(session_id, timestamp);
CREATE INDEX idx_cost_log_timestamp ON cost_log(timestamp);

CREATE INDEX idx_debug_log_level ON debug_log(level, timestamp);
CREATE INDEX idx_debug_log_timestamp ON debug_log(timestamp);
```

**Key Changes from Spec**:
1. ✅ Added CHECK constraints for data validation
2. ✅ Split token counts for accurate cost tracking (input, output, cache_read, cache_write)
3. ✅ Stored images as BLOB in products table (simpler for MVP than file paths)
4. ✅ Added CASCADE delete for analyses when product deleted
5. ✅ Added comprehensive indexes for common query patterns

### Connection Management Pattern

**Decision**: One connection per request via dependency injection.

**Rationale**:
- SQLite doesn't benefit from connection pooling (file-based, not server-based)
- aiosqlite handles concurrency through internal queue
- Simple dependency injection pattern aligns with FastAPI best practices
- Easy to test with mock database

**Implementation**:

```python
# database.py
import aiosqlite
from typing import AsyncGenerator
from pathlib import Path

DATABASE_PATH = Path("data/style_assistant.db")

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Dependency for database connections.
    Creates one connection per request.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row  # Enable dict-like access
        await db.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
        yield db

async def init_database():
    """Initialize database schema on startup."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Read schema from file
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()

        await db.executescript(schema)
        await db.commit()
```

### Migration Strategy

**For MVP**: Simple SQL script executed on startup.

**For Production** (future):
- Use Alembic for versioned migrations
- Track schema version in settings table
- Automatic migration on backend start

**Current Approach**:
```python
# main.py startup event
@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("Database initialized")
```

---

## 3. AI Provider Abstraction

### Base Class Design

**Goal**: Support future AI providers (LM Studio, OpenRouter, OpenAI) without changing analysis logic.

**Architecture Decision**: Abstract base class with template method pattern.

### Interface Definition

```python
# ai_providers/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AIProvider(ABC):
    """
    Abstract base class for all AI providers.

    Subclasses must implement:
    - analyze_product(): Full personalized analysis
    - basic_analysis(): Quick generic analysis
    - test_connection(): Verify API connectivity
    """

    @abstractmethod
    async def analyze_product(
        self,
        product_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Perform full style analysis on a product.

        Args:
            product_data: Extracted product information
            user_profile: User's style preferences (None for basic mode)
            use_cache: Whether to use prompt caching (if supported)

        Returns:
            {
                "analysis": {...},  # Analysis JSON matching schema
                "tokens": {
                    "input": int,
                    "output": int,
                    "cache_read": int,
                    "cache_write": int
                },
                "cost_usd": float,
                "model_used": str
            }
        """
        pass

    @abstractmethod
    async def basic_analysis(
        self,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform basic (non-personalized) analysis.

        Args:
            product_data: Extracted product information

        Returns:
            Same format as analyze_product()
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if API is reachable and credentials are valid.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def calculate_cost(self, tokens: Dict[str, int], model: str) -> float:
        """
        Calculate cost in USD from token usage.

        Args:
            tokens: Dict with input, output, cache_read, cache_write counts
            model: Model identifier

        Returns:
            Cost in USD
        """
        pass
```

### Claude Implementation

```python
# ai_providers/claude.py
import anthropic
from typing import Optional, Dict, Any
from .base import AIProvider
from .prompts import get_system_prompt, get_analysis_schema, get_product_context

class ClaudeProvider(AIProvider):
    """Claude API implementation with prompt caching support."""

    # Model identifiers
    SONNET_4_5 = "claude-sonnet-4.5-20250929"
    HAIKU_4_5 = "claude-haiku-4.5-20250929"

    # Pricing per million tokens (USD)
    PRICING = {
        SONNET_4_5: {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,    # 90% discount
            "cache_write": 3.75    # 25% markup
        },
        HAIKU_4_5: {
            "input": 1.00,
            "output": 5.00,
            "cache_read": 0.10,
            "cache_write": 1.25
        }
    }

    def __init__(self, api_key: str, enable_cache: bool = True):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.enable_cache = enable_cache

    async def analyze_product(
        self,
        product_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Full personalized analysis using Sonnet 4.5."""
        model = self.SONNET_4_5

        # Build system messages with caching
        system_messages = self._build_system_messages(
            user_profile=user_profile,
            use_cache=use_cache and self.enable_cache
        )

        # Call Claude API
        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_messages,
            messages=[{
                "role": "user",
                "content": f"Analyze this product:\n{json.dumps(product_data, indent=2)}"
            }],
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31"
            } if use_cache and self.enable_cache else {}
        )

        # Extract and return results
        return self._process_response(response, model)

    async def basic_analysis(
        self,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic analysis using Haiku 4.5 (no profile)."""
        model = self.HAIKU_4_5

        system_messages = self._build_system_messages(
            user_profile=None,
            use_cache=self.enable_cache
        )

        response = self.client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_messages,
            messages=[{
                "role": "user",
                "content": f"Provide basic analysis:\n{json.dumps(product_data, indent=2)}"
            }],
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31"
            } if self.enable_cache else {}
        )

        return self._process_response(response, model)

    def _build_system_messages(
        self,
        user_profile: Optional[Dict[str, Any]],
        use_cache: bool
    ) -> list:
        """Build system messages with cache breakpoints."""
        messages = [
            {
                "type": "text",
                "text": get_system_prompt()
            }
        ]

        # Cache breakpoint 1: User profile (if provided)
        if user_profile:
            messages.append({
                "type": "text",
                "text": f"USER PROFILE:\n{json.dumps(user_profile, indent=2)}",
                "cache_control": {"type": "ephemeral"} if use_cache else None
            })

        # Cache breakpoint 2: Analysis schema
        messages.append({
            "type": "text",
            "text": get_analysis_schema(),
            "cache_control": {"type": "ephemeral"} if use_cache else None
        })

        # Cache breakpoint 3: Product context (optional, for future use)
        # messages.append({
        #     "type": "text",
        #     "text": get_product_context(),
        #     "cache_control": {"type": "ephemeral"} if use_cache else None
        # })

        return messages

    def _process_response(self, response, model: str) -> Dict[str, Any]:
        """Extract analysis and token usage from API response."""
        usage = response.usage

        tokens = {
            "input": usage.input_tokens,
            "output": usage.output_tokens,
            "cache_read": getattr(usage, "cache_read_input_tokens", 0),
            "cache_write": getattr(usage, "cache_creation_input_tokens", 0)
        }

        cost = self.calculate_cost(tokens, model)

        # Parse JSON from response
        analysis_text = response.content[0].text
        analysis_data = json.loads(analysis_text)

        return {
            "analysis": analysis_data,
            "tokens": tokens,
            "cost_usd": cost,
            "model_used": model
        }

    def calculate_cost(self, tokens: Dict[str, int], model: str) -> float:
        """Calculate cost from token usage."""
        pricing = self.PRICING[model]

        cost = (
            tokens["input"] * pricing["input"] / 1_000_000 +
            tokens["output"] * pricing["output"] / 1_000_000 +
            tokens["cache_read"] * pricing["cache_read"] / 1_000_000 +
            tokens["cache_write"] * pricing["cache_write"] / 1_000_000
        )

        return round(cost, 6)  # Round to 6 decimal places

    async def test_connection(self) -> bool:
        """Test Claude API connectivity."""
        try:
            response = self.client.messages.create(
                model=self.HAIKU_4_5,
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            return True
        except Exception:
            return False
```

### Adding New Providers

**Example: LM Studio Provider (Future)**

```python
# ai_providers/lmstudio.py
from .base import AIProvider

class LMStudioProvider(AIProvider):
    """Local LM Studio implementation."""

    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url

    async def analyze_product(self, product_data, user_profile=None, use_cache=True):
        # Implementation using LM Studio's OpenAI-compatible API
        pass

    # ... implement other abstract methods
```

**Usage in main.py**:

```python
# Easy to swap providers
def get_ai_provider(settings: Settings = Depends(get_settings)) -> AIProvider:
    provider_type = settings.ai_provider  # 'claude', 'lmstudio', etc.

    if provider_type == 'claude':
        return ClaudeProvider(api_key=settings.claude_api_key)
    elif provider_type == 'lmstudio':
        return LMStudioProvider(base_url=settings.lmstudio_url)
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
```

---

## 4. API Endpoints

### Endpoint Definitions

```python
# All routes prefixed with /api/v1

# Analysis domain
POST   /api/v1/analyze              # Analyze product with optional profile
POST   /api/v1/test-connection      # Test Claude API connectivity

# Cost tracking domain
GET    /api/v1/costs/session/{session_id}   # Session cost breakdown
GET    /api/v1/costs/total                  # All-time costs (TODO)

# Health check
GET    /health                      # Backend health status
```

### Request/Response Models

```python
# analysis/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ProductData(BaseModel):
    """Product information extracted from e-commerce site."""
    url: str
    site: str = Field(..., pattern="^(uniqlo)$")  # Extensible for future sites
    title: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: str = "USD"
    description: Optional[str] = None
    materials: Optional[str] = None
    category: Optional[str] = None
    colors: List[str] = []
    sizes: List[str] = []
    images: List[str] = []  # URLs (will be downloaded and converted)

class AnalysisRequest(BaseModel):
    """Request to analyze a product."""
    product_data: ProductData
    user_profile: Optional[Dict[str, Any]] = None  # Null for basic mode
    mode: str = Field("full", pattern="^(full|basic)$")
    use_cache: bool = True
    session_id: str  # UUID from browser extension

class AnalysisResponse(BaseModel):
    """Analysis result with cost information."""
    analysis_data: Dict[str, Any]  # Matches spec's analysis_data schema
    cost_usd: float
    tokens_used: Dict[str, int]
    model_used: str
    cached: bool  # True if result from database cache
    profile_version: Optional[str] = None  # Hash used for caching

class TestConnectionRequest(BaseModel):
    """Test API connection."""
    api_key: str

class TestConnectionResponse(BaseModel):
    """Connection test result."""
    status: str  # "ok" or "error"
    message: Optional[str] = None
```

### Error Response Format

```python
# core/exceptions.py
class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str  # Error type/class name
    message: str  # Human-readable message
    detail: Optional[Dict[str, Any]] = None  # Additional context
    timestamp: str  # ISO 8601 timestamp
```

**Example Error Responses**:

```json
// 401 Unauthorized
{
    "error": "AuthenticationError",
    "message": "Invalid or missing API key",
    "timestamp": "2025-11-11T10:30:00Z"
}

// 500 Internal Server Error
{
    "error": "AIProviderError",
    "message": "Claude API returned an error",
    "detail": {
        "provider": "claude",
        "status_code": 429,
        "retry_after": 60
    },
    "timestamp": "2025-11-11T10:30:00Z"
}

// 400 Bad Request
{
    "error": "ValidationError",
    "message": "Invalid product data",
    "detail": {
        "field": "price",
        "error": "must be non-negative"
    },
    "timestamp": "2025-11-11T10:30:00Z"
}
```

### Dependency Chains

```
Route Handler
    ↓ Depends on
AnalysisService
    ↓ Depends on
[ProductService, AIProvider, CostService]
    ↓ Depends on
[DB Connection, Settings]
```

**Implementation**:

```python
# analysis/router.py
from fastapi import APIRouter, Depends, HTTPException
from analysis.schemas import AnalysisRequest, AnalysisResponse
from analysis.service import AnalysisService
from core.dependencies import get_db, get_settings

router = APIRouter()

def get_analysis_service(
    db: aiosqlite.Connection = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    product_service: ProductService = Depends(get_product_service),
    cost_service: CostService = Depends(get_cost_service)
) -> AnalysisService:
    """Dependency that constructs AnalysisService with all dependencies."""
    return AnalysisService(db, ai_provider, product_service, cost_service)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_product(
    request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analyze a product with personalized or basic style matching.

    - Checks cache for existing analysis (based on product + profile version)
    - If cache miss, calls AI provider with prompt caching
    - Stores result in database
    - Logs cost to cost_log table
    """
    try:
        result = await service.analyze(request)
        return result
    except Exception as e:
        # Exception middleware will handle this
        raise
```

---

## 5. Prompt Caching Strategy

### Cache Breakpoint Structure

**Decision**: Use 3 cache breakpoints (within Claude's 4-breakpoint limit).

**Breakpoints**:
1. **System Prompt** (~500 tokens) - Base instructions, never changes
2. **User Profile** (~1,500-2,000 tokens) - Changes when user retakes quiz
3. **Analysis Schema** (~1,500 tokens) - Output format, never changes

**Why Not 4 Breakpoints?**
- Product context would be breakpoint 4, but it's too small (<500 tokens)
- Better to merge product context into system prompt
- Save breakpoint budget for future needs (e.g., site-specific instructions)

### Profile Versioning Approach

**Decision**: Use SHA-256 hash of normalized profile JSON, truncated to 16 characters.

**Rationale**:
- Deterministic: Same profile always produces same hash
- Compact: 16 chars sufficient for collision avoidance at our scale
- Fast: SHA-256 is performant for small JSON blobs
- Database-friendly: Fits comfortably in TEXT column

**Implementation**:

```python
# profiles/versioning.py
import hashlib
import json

def get_profile_version(profile_data: dict) -> str:
    """
    Generate version hash for profile data.

    Uses SHA-256 hash of normalized JSON to ensure:
    - Same profile always produces same hash
    - Different profiles produce different hashes
    - Hash is compact (16 chars) and database-friendly

    Args:
        profile_data: User profile dictionary

    Returns:
        16-character hex hash
    """
    # Normalize JSON (sorted keys, no whitespace)
    normalized = json.dumps(profile_data, sort_keys=True, separators=(',', ':'))

    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))

    # Return first 16 characters (64 bits)
    return hash_obj.hexdigest()[:16]
```

**Example**:
```python
profile = {
    "fit_preferences": ["oversized", "relaxed"],
    "color_palette": ["black", "white", "earth_tones"]
}

version = get_profile_version(profile)  # "7f4a3b2c1d5e6a8b"

# Store in analyses table
INSERT INTO analyses (..., profile_version) VALUES (..., '7f4a3b2c1d5e6a8b')
```

### Cache Invalidation Logic

**Database Cache** (analyses table):
1. User retakes quiz → New profile data
2. Generate new profile version hash
3. Cache lookups using new hash miss
4. New analyses created and cached with new hash
5. Old analyses remain in DB (can show "based on old profile" message)

**Claude Prompt Cache** (5-minute TTL):
1. First request: Cache WRITE (25% markup on tokens)
2. Subsequent requests within 5 minutes: Cache READ (90% discount)
3. Each read refreshes the 5-minute TTL
4. After 5 minutes of inactivity: Cache expires, next request creates new cache

**Cache Hit Logic**:

```python
# analysis/cache.py
async def get_cached_analysis(
    db: aiosqlite.Connection,
    product_url: str,
    profile_version: Optional[str],
    analysis_type: str
) -> Optional[Dict[str, Any]]:
    """
    Look up cached analysis in database.

    Args:
        db: Database connection
        product_url: Product URL to look up
        profile_version: Profile hash (None for basic mode)
        analysis_type: 'full' or 'basic'

    Returns:
        Cached analysis data or None if cache miss
    """
    # Find product by URL
    async with db.execute(
        "SELECT id FROM products WHERE product_url = ?",
        (product_url,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None  # Product not in cache
        product_id = row["id"]

    # Look up analysis
    query = """
        SELECT analysis_data, model_used, tokens_input, tokens_output, cost_usd
        FROM analyses
        WHERE product_id = ?
          AND profile_version = ?
          AND analysis_type = ?
        ORDER BY created_at DESC
        LIMIT 1
    """

    async with db.execute(
        query,
        (product_id, profile_version or "", analysis_type)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None  # No cached analysis for this profile version

        return {
            "analysis_data": json.loads(row["analysis_data"]),
            "model_used": row["model_used"],
            "tokens_used": {
                "input": row["tokens_input"],
                "output": row["tokens_output"]
            },
            "cost_usd": row["cost_usd"],
            "cached": True
        }
```

### Expected Cost Savings Calculation

**Scenario**: User browses 10 products in one session (profile stays constant).

**Without Prompt Caching**:
```
Product 1: 3,500 input tokens × $3.00/M = $0.0105
Product 2: 3,500 input tokens × $3.00/M = $0.0105
...
Product 10: Same

Total input cost: $0.105 (for 10 products)
```

**With Prompt Caching** (after first request):
```
Product 1 (cache write):
  - System + Profile + Schema: 3,000 tokens × $3.75/M (cache write) = $0.01125
  - Product data: 500 tokens × $3.00/M = $0.0015
  - Total: $0.01275

Products 2-10 (cache read):
  - Cached (3,000 tokens) × $0.30/M = $0.0009
  - Product data: 500 tokens × $3.00/M = $0.0015
  - Total per product: $0.0024
  - 9 products: $0.0216

Total input cost: $0.01275 + $0.0216 = $0.03435
```

**Savings**: $0.105 - $0.03435 = **$0.071** (**67% reduction**)

**Note**: Output costs are the same ($15/M for Sonnet), so total savings is lower (~50-55% overall).

---

## 6. Component Contracts

### Database Layer API

**Purpose**: Abstract SQLite operations into reusable, testable functions.

**Location**: Each domain's `models.py` file.

**Example Contract**:

```python
# products/models.py

async def get_product_by_url(
    db: aiosqlite.Connection,
    url: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve product by URL.

    Args:
        db: Database connection
        url: Product URL

    Returns:
        Product dict or None if not found
    """
    pass

async def create_product(
    db: aiosqlite.Connection,
    product_data: Dict[str, Any]
) -> int:
    """
    Insert new product into database.

    Args:
        db: Database connection
        product_data: Product information

    Returns:
        Inserted product ID
    """
    pass

async def update_product_last_seen(
    db: aiosqlite.Connection,
    product_id: int
) -> None:
    """
    Update last_seen timestamp for product.

    Args:
        db: Database connection
        product_id: Product ID
    """
    pass
```

### AI Provider Interface

**Contract**: See "AI Provider Abstraction" section above.

**Key Methods**:
- `analyze_product()` - Full personalized analysis
- `basic_analysis()` - Quick generic analysis
- `test_connection()` - Health check
- `calculate_cost()` - Token usage → USD

### Service Layer Responsibilities

**Purpose**: Business logic layer between routers and data access.

**Responsibilities**:
1. ✅ Orchestrate multiple data operations
2. ✅ Implement business rules (e.g., cache lookup before AI call)
3. ✅ Handle domain-specific errors
4. ✅ Transform data between schemas and database models
5. ✅ Log operations for debugging

**Example Service**:

```python
# analysis/service.py
class AnalysisService:
    """Business logic for product analysis."""

    def __init__(
        self,
        db: aiosqlite.Connection,
        ai_provider: AIProvider,
        product_service: ProductService,
        cost_service: CostService
    ):
        self.db = db
        self.ai_provider = ai_provider
        self.product_service = product_service
        self.cost_service = cost_service

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Perform product analysis with caching.

        Business logic:
        1. Get or create product in database
        2. Generate profile version hash (if profile provided)
        3. Check for cached analysis
        4. If cache miss, call AI provider
        5. Store analysis in database
        6. Log cost
        7. Return result
        """
        # Step 1: Get or create product
        product = await self.product_service.get_or_create(
            request.product_data
        )

        # Step 2: Profile version
        profile_version = None
        if request.user_profile:
            profile_version = get_profile_version(request.user_profile)

        # Step 3: Check cache
        cached = await get_cached_analysis(
            self.db,
            request.product_data.url,
            profile_version,
            request.mode
        )

        if cached:
            return AnalysisResponse(**cached)

        # Step 4: Call AI provider
        if request.mode == "full":
            result = await self.ai_provider.analyze_product(
                request.product_data.dict(),
                request.user_profile,
                request.use_cache
            )
        else:
            result = await self.ai_provider.basic_analysis(
                request.product_data.dict()
            )

        # Step 5: Store analysis
        await store_analysis(
            self.db,
            product["id"],
            profile_version or "",
            result["model_used"],
            request.mode,
            result["analysis"],
            result["tokens"],
            result["cost_usd"]
        )

        # Step 6: Log cost
        await self.cost_service.log_cost(
            session_id=request.session_id,
            model=result["model_used"],
            tokens=result["tokens"],
            cost_usd=result["cost_usd"],
            request_type=request.mode
        )

        # Step 7: Return result
        return AnalysisResponse(
            analysis_data=result["analysis"],
            cost_usd=result["cost_usd"],
            tokens_used=result["tokens"],
            model_used=result["model_used"],
            cached=False,
            profile_version=profile_version
        )
```

### Router Responsibilities

**Purpose**: HTTP request/response handling only.

**Responsibilities**:
1. ✅ Parse and validate requests (Pydantic models)
2. ✅ Call service layer
3. ✅ Format responses
4. ✅ Handle HTTP-specific concerns (status codes, headers)
5. ❌ NO business logic
6. ❌ NO direct database access
7. ❌ NO AI provider calls

**Anti-pattern**:
```python
# ❌ BAD: Business logic in router
@router.post("/analyze")
async def analyze(request: AnalysisRequest, db = Depends(get_db)):
    # Check cache
    cached = await db.execute(...)  # ❌ Direct DB access
    if cached:
        return cached

    # Call AI
    ai = ClaudeProvider(...)  # ❌ Direct AI instantiation
    result = await ai.analyze(...)  # ❌ Business logic here

    return result
```

**Correct pattern**:
```python
# ✅ GOOD: Thin router delegates to service
@router.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service)
):
    result = await service.analyze(request)
    return result
```

---

## 7. Error Handling Strategy

### Exception Hierarchy

```python
# core/exceptions.py

class StyleAssistantException(Exception):
    """Base exception for all custom exceptions."""
    def __init__(self, message: str, status_code: int = 500, detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

# Domain-specific exceptions
class DatabaseError(StyleAssistantException):
    """Database operation failed."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message, status_code=500, detail=detail)

class AIProviderError(StyleAssistantException):
    """AI provider API error."""
    def __init__(self, message: str, status_code: int = 500, detail: dict = None):
        super().__init__(message, status_code=status_code, detail=detail)

class CacheError(StyleAssistantException):
    """Cache lookup or storage failed."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message, status_code=500, detail=detail)

class ValidationError(StyleAssistantException):
    """Request validation failed."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message, status_code=400, detail=detail)

class AuthenticationError(StyleAssistantException):
    """Authentication failed."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message, status_code=401, detail=detail)

class RateLimitError(AIProviderError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Rate limit exceeded",
            status_code=429,
            detail={"retry_after": retry_after}
        )
```

### Error Middleware

```python
# core/middleware.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def error_handling_middleware(request: Request, call_next):
    """
    Global error handler middleware.

    Catches all exceptions and returns standardized error responses.
    """
    try:
        response = await call_next(request)
        return response

    except StyleAssistantException as e:
        # Log custom exceptions
        logger.error(
            f"{e.__class__.__name__}: {e.message}",
            extra={"detail": e.detail, "path": request.url.path}
        )

        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.__class__.__name__,
                "message": e.message,
                "detail": e.detail,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    except Exception as e:
        # Log unexpected exceptions with full traceback
        logger.exception(
            f"Unhandled exception: {str(e)}",
            extra={"path": request.url.path}
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

# Register in main.py
app.middleware("http")(error_handling_middleware)
```

### Logging Integration

**Strategy**: Structured logging with context.

```python
# utils/logging_utils.py
import logging
import sys

def setup_logging(log_level: str = "INFO"):
    """
    Configure application logging.

    Logs to stdout with structured format for parsing.
    """
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )

    # Set library log levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

# Usage in main.py
setup_logging(log_level="INFO")
logger = logging.getLogger("style_assistant")
```

### Graceful Degradation

**Principles**:
1. Never crash the entire backend
2. Return partial results when possible
3. Log errors but continue operation
4. Provide user-friendly error messages

**Example**:
```python
# If image download fails, continue without images
try:
    images = await download_product_images(product_data.images)
except Exception as e:
    logger.warning(f"Image download failed: {e}")
    images = []  # Continue without images

# Store product without images
await store_product(product_data, images=[])
```

---

## 8. Implementation Order

### Phase 1: Core Infrastructure (Week 1)

**Goal**: Get basic backend running with database and AI integration.

**Tasks**:
1. ✅ Initialize FastAPI project structure
2. ✅ Create `database.py` with schema initialization
3. ✅ Implement `core/dependencies.py` (get_db, get_settings)
4. ✅ Create AI provider abstraction (`ai_providers/base.py`)
5. ✅ Implement Claude provider with prompt caching
6. ✅ Add error handling middleware
7. ✅ Create health check endpoint

**Deliverable**: Backend starts, connects to SQLite, can call Claude API.

**Testing**: Manual `curl` requests to `/health`.

---

### Phase 2: Analysis Domain (Week 2)

**Goal**: Product analysis working end-to-end.

**Tasks**:
1. ✅ Create `products/` domain (models, schemas, service)
2. ✅ Create `profiles/` domain with versioning
3. ✅ Create `analysis/` domain (router, service, cache)
4. ✅ Implement `POST /api/v1/analyze` endpoint
5. ✅ Add cache lookup logic
6. ✅ Implement prompt caching with 3 breakpoints
7. ✅ Test with sample product data

**Deliverable**: Can analyze products with/without profile, results cached.

**Testing**: Integration tests with mock AI provider.

---

### Phase 3: Cost Tracking (Week 3)

**Goal**: Cost logging and retrieval working.

**Tasks**:
1. ✅ Create `costs/` domain (models, schemas, service, router)
2. ✅ Implement `GET /api/v1/costs/session/{id}` endpoint
3. ✅ Add cost logging to analysis service
4. ✅ Implement cost aggregation (session, all-time)
5. ✅ Test cost calculations match expected values

**Deliverable**: Can track and query costs accurately.

**Testing**: Verify cost calculations with known token counts.

---

### Phase 4: Image Processing (Week 4)

**Goal**: Product images downloaded, converted, stored.

**Tasks**:
1. ✅ Implement `utils/image_processing.py`
2. ✅ Add image download to product service
3. ✅ Store WebP images in database BLOB
4. ✅ Test with various image formats and sizes

**Deliverable**: Product images stored efficiently.

**Testing**: Verify images <200KB, WebP format.

---

### Phase 5: Polish & Testing (Week 5)

**Goal**: Production-ready backend.

**Tasks**:
1. ✅ Comprehensive error handling everywhere
2. ✅ Add debug logging to all critical paths
3. ✅ Write unit tests for services
4. ✅ Write integration tests for endpoints
5. ✅ Performance testing (concurrent requests)
6. ✅ Documentation (API docs, setup guide)

**Deliverable**: Robust, tested, documented backend.

**Testing**: Full test suite with >80% coverage.

---

## Concerns & Risks

### 1. aiosqlite Performance Overhead

**Concern**: 15x slower `fetchone()` operations may impact cache lookups.

**Mitigation**:
- Use `fetchall()` for multi-row queries (minimal overhead)
- Cache lookups are infrequent (only on cache miss)
- Absolute performance impact is <50ms per request
- Non-blocking behavior more important than raw speed

**Risk Level**: Low

---

### 2. Prompt Cache Invalidation

**Concern**: User might update profile but not understand cache invalidation.

**Mitigation**:
- Profile versioning ensures new hash = new cache
- Old analyses marked with "Based on previous profile" in UI
- Provide "Refresh analysis" button to force new analysis

**Risk Level**: Medium (UX challenge, not technical)

---

### 3. Image Storage Bloat

**Concern**: Storing images as BLOBs in SQLite may cause database bloat.

**Mitigation**:
- Target 200KB per image with WebP compression
- Limit to 3-5 images per product
- Maximum ~1MB per product for images
- For 1,000 products = ~1GB database size (acceptable for local MVP)
- Future: Move to file storage or CDN if needed

**Risk Level**: Low for MVP, Medium long-term

---

### 4. Claude API Rate Limits

**Concern**: Heavy usage during browsing session may hit rate limits.

**Mitigation**:
- Database caching reduces API calls by 70-80%
- Graceful error handling with retry logic
- Rate limit errors return 429 with retry-after header
- Frontend implements exponential backoff

**Risk Level**: Low (caching helps significantly)

---

### 5. Concurrent Request Handling

**Concern**: aiosqlite serializes writes, may bottleneck under high concurrency.

**Mitigation**:
- Most operations are reads (cache lookups) which SQLite handles well
- Writes are infrequent (new analyses only on cache miss)
- Expected load: 1-5 concurrent requests (browser extension use case)
- If needed: Implement request queuing at application level

**Risk Level**: Low for MVP (single-user use case)

---

### 6. Prompt Token Count Variability

**Concern**: Token counts may vary, affecting cache effectiveness and costs.

**Mitigation**:
- Use Claude's token counting API for accuracy
- Monitor actual vs. expected token usage
- Set max_tokens limits to prevent runaway costs
- Log detailed token breakdown for debugging

**Risk Level**: Medium (requires monitoring)

---

### 7. Profile Schema Evolution

**Concern**: Adding new quiz questions breaks existing profile hashes.

**Mitigation**:
- Use semantic versioning in profile JSON (`"version": "1.0"`)
- Migration logic to update old profiles
- Keep old analyses valid (show "Based on v1.0 profile")
- Optional: Re-analyze old products with new profile on demand

**Risk Level**: Medium (design migration strategy early)

---

## Next Steps: Development Phase

**Status**: Architecture validated and finalized.

**Ready for**: Core Infrastructure Subagent (Phase 1 implementation).

### Context for Next Subagent

**Files to Reference**:
1. This document (`backend_architecture.md`) - Architecture decisions
2. Project spec (`StyleAssistantSpec.md`) - Feature requirements
3. Technical research (`backend_technical_research.md`) - Implementation details
4. `pyproject.toml` - Dependencies already configured

**Key Decisions to Follow**:
1. ✅ Use hybrid directory structure (domain-driven + utilities)
2. ✅ Implement AI provider base class first, then Claude provider
3. ✅ Use aiosqlite with dependency injection (get_db)
4. ✅ Create schema.sql file for database initialization
5. ✅ Implement 3-breakpoint prompt caching (system, profile, schema)
6. ✅ Use SHA-256 profile versioning (16 chars)
7. ✅ Service layer pattern (thin routers, business logic in services)
8. ✅ Middleware-based error handling

**Implementation Order**:
1. Project structure and dependencies
2. Database layer (schema, connection management)
3. AI provider abstraction and Claude implementation
4. Core dependencies (settings, error middleware)
5. Health check endpoint

**Testing Requirements**:
- Unit tests for cost calculator
- Integration tests for database operations
- Mock AI provider for testing services
- Health check endpoint verification

---

## Appendix: Quick Reference

### Command Cheat Sheet

```bash
# Start backend
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .

# Initialize database
uv run python -c "from database import init_database; import asyncio; asyncio.run(init_database())"
```

### Key Files Checklist

```
✅ backend/main.py              - FastAPI app
✅ backend/database.py          - DB connection
✅ backend/schema.sql           - Database schema
✅ backend/config.py            - Settings
✅ backend/core/dependencies.py - DI functions
✅ backend/core/middleware.py   - Error handling
✅ backend/ai_providers/base.py - Abstract provider
✅ backend/ai_providers/claude.py - Claude implementation
```

---

**Document Status**: Final - Ready for Implementation
**Next Phase**: Development Phase - Core Infrastructure
**Estimated Time to MVP**: 5 weeks


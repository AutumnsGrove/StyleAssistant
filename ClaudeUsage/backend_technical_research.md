# Backend Technical Research

**Project**: Style Assistant Browser Extension
**Focus**: FastAPI Backend, SQLite Database, Claude API Integration
**Date**: 2025-11-11
**Research Phase**: Technical Foundation

---

## Executive Summary

This document provides technical research findings and implementation recommendations for the Style Assistant backend. The backend will use FastAPI (Python), SQLite for data persistence, and Anthropic's Claude API with prompt caching to provide personalized style analysis while minimizing costs.

**Key Findings**:
- Domain-driven FastAPI structure recommended over type-based organization
- aiosqlite enables async SQLite operations but with ~15x overhead on single-row operations
- Claude prompt caching can reduce costs by up to 90% with proper implementation
- Dependency injection patterns critical for testability and maintainability
- Connection pooling essential for high-load scenarios

---

## 1. FastAPI Project Structure

### Research Findings

Modern FastAPI applications (2025) favor **domain-driven structure** over traditional file-type organization. Instead of separating all routes, models, and schemas across the entire project, each feature domain contains its own complete set of components.

### Two Main Approaches

#### File-Type Structure (Traditional)
```
backend/
├── routers/
│   ├── users.py
│   ├── products.py
├── models/
│   ├── user.py
│   ├── product.py
├── schemas/
│   ├── user.py
│   ├── product.py
```

**Use Case**: Microservices, small projects with few domains

#### Domain-Driven Structure (Recommended)
```
backend/
├── users/
│   ├── router.py
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
│   ├── dependencies.py
├── products/
│   ├── router.py
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
```

**Use Case**: Monolithic applications, projects with multiple domains

**Benefits**:
- Better code locality - all related code in one place
- Easier to understand feature boundaries
- Simpler refactoring and testing
- Scales better for larger projects

### Recommended Structure for Style Assistant

Based on the project requirements, the following structure is recommended:

```
backend/
├── main.py                     # FastAPI app initialization
├── config.py                   # Configuration, settings, constants
├── database.py                 # Database connection & session management
│
├── core/                       # Shared utilities
│   ├── dependencies.py         # Global dependencies
│   ├── exceptions.py           # Custom exceptions
│   └── security.py             # API key validation
│
├── ai_providers/               # AI provider abstraction
│   ├── base.py                 # Abstract base class
│   ├── claude.py               # Claude implementation
│   ├── schemas.py              # Common AI request/response models
│   └── cost_calculator.py      # Cost calculation utilities
│
├── analysis/                   # Analysis domain
│   ├── router.py               # /api/analyze endpoints
│   ├── models.py               # DB models (analyses table)
│   ├── schemas.py              # Pydantic request/response models
│   ├── service.py              # Business logic
│   └── dependencies.py         # Analysis-specific dependencies
│
├── products/                   # Product domain
│   ├── models.py               # DB models (products table)
│   ├── schemas.py              # Product schemas
│   ├── service.py              # Product extraction/storage logic
│   └── extractors/             # Site-specific extractors
│       ├── base.py
│       └── uniqlo.py
│
├── profiles/                   # User profile domain
│   ├── models.py               # DB models (user_profile table)
│   ├── schemas.py              # Profile schemas
│   └── service.py              # Profile management
│
├── costs/                      # Cost tracking domain
│   ├── router.py               # /api/costs endpoints
│   ├── models.py               # DB models (cost_log table)
│   ├── schemas.py              # Cost schemas
│   └── service.py              # Cost calculation/aggregation
│
└── utils/                      # Shared utilities
    ├── image_processing.py     # WebP conversion, compression
    └── hashing.py              # Profile version hashing
```

### Best Practices

1. **Separation of Concerns**: Keep routers thin - delegate business logic to service layers
2. **Dependency Injection**: Use FastAPI's `Depends()` for database sessions, authentication, etc.
3. **Pydantic Models**: Use separate schemas for requests, responses, and database models
4. **API Versioning**: Prefix routes with `/api/v1` for future compatibility
5. **Error Handling**: Create custom exception handlers for consistent error responses

### Code Examples

**main.py (Application Entry Point)**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analysis.router import router as analysis_router
from costs.router import router as costs_router

app = FastAPI(
    title="Style Assistant API",
    version="1.0.0",
    description="AI-powered style analysis backend"
)

# CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["moz-extension://*"],  # Firefox extension
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
app.include_router(costs_router, prefix="/api/v1", tags=["costs"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**Service Layer Pattern**
```python
# analysis/service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from analysis.models import Analysis
from analysis.schemas import AnalysisRequest, AnalysisResponse
from ai_providers.base import AIProvider
from products.service import ProductService

class AnalysisService:
    def __init__(self, db: AsyncSession, ai_provider: AIProvider):
        self.db = db
        self.ai_provider = ai_provider

    async def analyze_product(
        self,
        request: AnalysisRequest,
        profile_version: str
    ) -> AnalysisResponse:
        # Check cache first
        cached = await self._get_cached_analysis(
            request.product_data.url,
            profile_version
        )
        if cached:
            return cached

        # Call AI provider
        analysis_data = await self.ai_provider.analyze_product(
            request.product_data,
            request.user_profile
        )

        # Store in database
        await self._store_analysis(analysis_data, profile_version)

        return analysis_data
```

---

## 2. SQLite with Python & FastAPI

### Research Findings

SQLite is a lightweight, serverless database perfect for local-first applications. For async FastAPI applications, there are trade-offs between using synchronous `sqlite3` and asynchronous `aiosqlite`.

### Performance Comparison: sqlite3 vs aiosqlite

**sqlite3 (Synchronous)**
- Part of Python standard library
- Excellent performance for all operations
- Blocks the event loop in async applications
- Best for: Synchronous apps, CLI tools

**aiosqlite (Asynchronous)**
- Non-blocking async/await support
- ~15x slower for single-row operations (`fetchone()`)
- Similar performance for bulk operations (`fetchall()`, `fetchmany()`)
- Overhead from thread synchronization
- Best for: Async FastAPI applications where you need concurrent request handling

### Performance Overhead

The slowdown in aiosqlite comes from its architecture:
- Uses a single shared thread per connection
- All actions execute through a shared request queue
- Thread synchronization adds overhead, especially for `fetchone()` operations
- Bulk operations (`fetchall()`, `fetchmany()`) have minimal overhead

### Recommendation for Style Assistant

**Use aiosqlite** despite the overhead because:
1. FastAPI is async-first - blocking operations would harm concurrency
2. Most queries will be bulk operations (fetching full analysis data)
3. Product catalog and analysis results are read-heavy operations
4. Small dataset size means absolute performance impact is minimal
5. Non-blocking behavior is more important than raw speed for web API

### Connection Management

**No Connection Pooling Needed for SQLite**

Unlike PostgreSQL or MySQL, SQLite doesn't benefit from traditional connection pooling because:
- SQLite is a file-based database, not a server
- Connections are lightweight (just file handles)
- SQLite has built-in write serialization
- Multiple connections can read concurrently, but writes are serialized

**Best Practice**: Create one connection per request using dependency injection:

```python
# database.py
import aiosqlite
from typing import AsyncGenerator

DATABASE_URL = "database.db"

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependency for database connections."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row  # Enable dict-like access
        yield db
```

**Usage in Routes**:
```python
from fastapi import Depends
from database import get_db

@app.get("/products/{product_id}")
async def get_product(
    product_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None
```

### Schema Design Best Practices

**1. Use JSON Columns for Complex Data**

SQLite supports JSON storage and has JSON functions for querying:

```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    analysis_data TEXT NOT NULL,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query JSON fields
SELECT json_extract(analysis_data, '$.style_match_score') as score
FROM analyses
WHERE score > 80;
```

**2. Add Indexes for Common Queries**

```sql
-- Index for cache lookups
CREATE INDEX idx_analyses_product_profile
ON analyses(product_id, profile_version);

-- Index for cost queries by session
CREATE INDEX idx_cost_log_session
ON cost_log(session_id, timestamp);

-- Index for product URL lookups
CREATE UNIQUE INDEX idx_products_url
ON products(product_url);
```

**3. Enable Foreign Keys**

SQLite doesn't enforce foreign keys by default:

```python
async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.commit()
```

**4. Use Transactions for Multiple Operations**

```python
async def store_product_and_analysis(
    db: aiosqlite.Connection,
    product_data: dict,
    analysis_data: dict
):
    async with db.execute("BEGIN"):
        cursor = await db.execute(
            "INSERT INTO products (...) VALUES (...)",
            product_data
        )
        product_id = cursor.lastrowid

        await db.execute(
            "INSERT INTO analyses (...) VALUES (...)",
            (product_id, analysis_data)
        )
        await db.commit()
```

### Database Migration Strategy

For a small project, use simple SQL scripts:

```python
# database.py
async def init_database():
    """Initialize database schema."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        # Read schema file
        with open("schema.sql") as f:
            schema = f.read()
        await db.executescript(schema)
        await db.commit()
```

For production, consider using **Alembic** for migrations:
- Version-controlled schema changes
- Automatic migration generation
- Rollback support

---

## 3. Claude API Prompt Caching

### Research Findings

Anthropic's prompt caching feature can dramatically reduce costs and latency for applications with repetitive context. This is critical for the Style Assistant since user profiles and extraction schemas remain constant across requests.

### How Prompt Caching Works

**Cache Mechanism**:
- Specify content blocks to cache using `cache_control` parameter
- Cached content persists for 5 minutes (refreshed on each use)
- Maximum 4 cache breakpoints per request
- Minimum cacheable block size: ~1024 tokens

**Cost Reduction**:
- Cached tokens cost 90% less than regular input tokens
- Cache reads: 10% of base input price
- Can achieve up to 90% cost reduction on cached portions

**Latency Reduction**:
- Up to 85% faster response times for long prompts
- Especially beneficial for prompts >10,000 tokens

### Supported Models

Prompt caching is available for:
- Claude Opus 4.1
- **Claude Sonnet 4.5** (our primary model)
- Claude Sonnet 4
- **Claude Haiku 4.5** (our basic mode model)
- Claude Haiku 3.5, 3
- Claude Opus 3 (deprecated)

### Implementation for Style Assistant

**API Request Structure**:

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

response = client.messages.create(
    model="claude-sonnet-4.5-20250929",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a fashion and style analysis assistant."
        },
        {
            "type": "text",
            "text": f"User Profile: {json.dumps(user_profile)}",
            "cache_control": {"type": "ephemeral"}  # Cache user profile
        },
        {
            "type": "text",
            "text": ANALYSIS_SCHEMA,  # Instructions for analysis format
            "cache_control": {"type": "ephemeral"}  # Cache schema
        }
    ],
    messages=[
        {
            "role": "user",
            "content": f"Analyze this product: {json.dumps(product_data)}"
        }
    ],
    extra_headers={
        "anthropic-beta": "prompt-caching-2024-07-31"
    }
)
```

### Caching Strategy for Style Assistant

**What to Cache** (in order of cache breakpoints):

1. **System Prompt** (~500 tokens)
   - Base instructions for the assistant role
   - General formatting guidelines

2. **User Profile** (~1,000-2,000 tokens)
   - Quiz results JSON
   - Style preferences
   - Priorities and avoidances
   - **Changes rarely** - perfect for caching

3. **Analysis Schema** (~1,500 tokens)
   - JSON schema for expected output format
   - Scoring guidelines
   - Pairing suggestion structure
   - **Never changes** - ideal for caching

4. **Product Context** (optional, ~500 tokens)
   - General product analysis instructions
   - Site-specific considerations

**What NOT to Cache**:
- Product data (changes every request)
- Dynamic prompts
- User messages

### Cost Calculation Formula

**Token Pricing** (per million tokens):

| Model | Input | Output | Cached Input (90% off) |
|-------|-------|--------|----------------------|
| Sonnet 4.5 | $3.00 | $15.00 | $0.30 |
| Haiku 4.5 | $1.00 | $5.00 | $0.10 |

**Example Calculation**:

```python
# Without caching
user_profile_tokens = 1500
schema_tokens = 1500
product_tokens = 500
output_tokens = 800

cost_without_cache = (
    (1500 + 1500 + 500) / 1_000_000 * 3.00 +  # Input
    800 / 1_000_000 * 15.00  # Output
)
# = $0.0105 + $0.012 = $0.0225

# With caching (after first request)
cache_read_tokens = 1500 + 1500  # Profile + schema
new_input_tokens = 500  # Only product data

cost_with_cache = (
    3000 / 1_000_000 * 0.30 +  # Cache read (90% discount)
    500 / 1_000_000 * 3.00 +   # New input
    800 / 1_000_000 * 15.00    # Output
)
# = $0.0009 + $0.0015 + $0.012 = $0.0144

# Savings: $0.0225 - $0.0144 = $0.0081 (36% reduction)
```

### Cache Management Implementation

```python
# ai_providers/claude.py
class ClaudeProvider:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cache_enabled = True

    async def analyze_product(
        self,
        product_data: dict,
        user_profile: Optional[dict] = None,
        mode: str = "full"
    ):
        system_messages = [
            {
                "type": "text",
                "text": self._get_system_prompt()
            }
        ]

        # Add cached profile for personalized analysis
        if user_profile:
            system_messages.append({
                "type": "text",
                "text": f"USER PROFILE:\n{json.dumps(user_profile, indent=2)}",
                "cache_control": {"type": "ephemeral"}
            })

        # Add cached analysis schema
        system_messages.append({
            "type": "text",
            "text": self._get_analysis_schema(),
            "cache_control": {"type": "ephemeral"}
        })

        model = "claude-sonnet-4.5-20250929" if mode == "full" else "claude-haiku-4.5-20250929"

        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_messages,
            messages=[{
                "role": "user",
                "content": f"Analyze this product:\n{json.dumps(product_data)}"
            }],
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31"
            } if self.cache_enabled else {}
        )

        # Extract token usage for cost tracking
        usage = response.usage
        return {
            "analysis": json.loads(response.content[0].text),
            "tokens": {
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "cache_read": getattr(usage, "cache_read_input_tokens", 0),
                "cache_creation": getattr(usage, "cache_creation_input_tokens", 0)
            }
        }
```

### Token Counting

The API response includes detailed token usage:

```python
response.usage:
{
    "input_tokens": 500,           # New input tokens
    "output_tokens": 800,          # Generated tokens
    "cache_creation_input_tokens": 3000,  # First request only
    "cache_read_input_tokens": 3000       # Subsequent requests
}
```

**Cost Tracking**:
```python
def calculate_cost(usage, model: str) -> float:
    """Calculate cost from token usage."""
    pricing = {
        "claude-sonnet-4.5-20250929": {
            "input": 3.00 / 1_000_000,
            "output": 15.00 / 1_000_000,
            "cache_read": 0.30 / 1_000_000,
            "cache_write": 3.75 / 1_000_000  # 25% markup
        },
        "claude-haiku-4.5-20250929": {
            "input": 1.00 / 1_000_000,
            "output": 5.00 / 1_000_000,
            "cache_read": 0.10 / 1_000_000,
            "cache_write": 1.25 / 1_000_000
        }
    }

    p = pricing[model]
    cost = (
        usage.input_tokens * p["input"] +
        usage.output_tokens * p["output"] +
        getattr(usage, "cache_read_input_tokens", 0) * p["cache_read"] +
        getattr(usage, "cache_creation_input_tokens", 0) * p["cache_write"]
    )
    return cost
```

### Cache Invalidation Strategy

**Automatic Invalidation**:
- Cache expires after 5 minutes of no use
- Each cache read refreshes the TTL

**Manual Invalidation**:
- User profile changes → New profile version hash → Different cache key
- Schema updates → Increment schema version in prompt

**Profile Version Hashing**:
```python
import hashlib
import json

def get_profile_version(profile_data: dict) -> str:
    """Generate hash of profile for cache invalidation."""
    normalized = json.dumps(profile_data, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

Store this hash in the `analyses` table to detect when cached analyses are stale.

---

## 4. FastAPI Dependency Injection

### Research Findings

FastAPI's dependency injection system is one of its most powerful features, enabling clean separation of concerns, easy testing, and code reusability.

### Core Concepts

**What is Dependency Injection?**
- A design pattern where components receive their dependencies from external sources
- Reduces tight coupling between components
- Makes code more testable and maintainable
- FastAPI handles dependency resolution automatically

### Common Use Cases

1. **Database Sessions**: Inject database connections into routes
2. **Authentication**: Verify API keys or user tokens
3. **Configuration**: Provide settings to handlers
4. **Service Layers**: Inject business logic services
5. **Shared Resources**: Connection pools, caches, etc.

### Dependency Patterns

**Basic Function Dependency**:
```python
from fastapi import Depends

def get_api_key(api_key: str = Header(None)) -> str:
    """Validate API key from header."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    # Validate key
    return api_key

@app.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    api_key: str = Depends(get_api_key)
):
    # api_key is validated and injected
    pass
```

**Class-Based Dependencies**:
```python
class APIKeyValidator:
    def __init__(self, required: bool = True):
        self.required = required

    def __call__(self, api_key: str = Header(None)) -> str:
        if self.required and not api_key:
            raise HTTPException(status_code=401)
        return api_key

# Use in routes
@app.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    api_key: str = Depends(APIKeyValidator(required=True))
):
    pass
```

**Hierarchical Dependencies**:
```python
# Dependency chain
def get_db():
    """Provide database connection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_product_service(db: Session = Depends(get_db)):
    """Provide product service with db dependency."""
    return ProductService(db)

def get_analysis_service(
    db: Session = Depends(get_db),
    product_service: ProductService = Depends(get_product_service)
):
    """Provide analysis service with multiple dependencies."""
    return AnalysisService(db, product_service)

# Route uses only the top-level dependency
@app.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service)
):
    return await service.analyze(request)
```

### Dependency Scopes

FastAPI dependencies can have different lifetimes:

**Request-Scoped (Default)**:
- Created for each request
- Destroyed after response
- Most common for database sessions

**Singleton (Application-Scoped)**:
- Created once at startup
- Shared across all requests
- Use for configuration, connection pools

```python
# Singleton dependency
class Settings:
    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY")
        self.db_url = os.getenv("DATABASE_URL")

settings = Settings()  # Created once

def get_settings() -> Settings:
    return settings  # Same instance every time
```

### Testing with Dependency Overrides

One of the best features - easily mock dependencies for testing:

```python
from fastapi.testclient import TestClient

# Production dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test dependency (mock)
def get_db_override():
    return MockDatabase()

# Override in tests
app.dependency_overrides[get_db] = get_db_override

client = TestClient(app)
response = client.post("/analyze", json={...})
# Uses mock database instead of real one
```

### Recommendations for Style Assistant

**1. Database Session Dependency**:
```python
# core/dependencies.py
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        yield db
```

**2. AI Provider Dependency**:
```python
# core/dependencies.py
from ai_providers.claude import ClaudeProvider

def get_ai_provider(
    settings: Settings = Depends(get_settings)
) -> ClaudeProvider:
    return ClaudeProvider(api_key=settings.claude_api_key)
```

**3. Service Layer Dependencies**:
```python
# analysis/dependencies.py
def get_analysis_service(
    db: aiosqlite.Connection = Depends(get_db),
    ai_provider: ClaudeProvider = Depends(get_ai_provider)
) -> AnalysisService:
    return AnalysisService(db, ai_provider)
```

**4. API Key Validation**:
```python
# core/dependencies.py
async def verify_extension_key(
    x_api_key: str = Header(None)
) -> str:
    """Verify request is from our browser extension."""
    if not x_api_key or x_api_key != settings.extension_secret:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key
```

**5. Usage in Routes**:
```python
# analysis/router.py
from core.dependencies import get_db, verify_extension_key
from analysis.dependencies import get_analysis_service

router = APIRouter()

@router.post("/analyze")
async def analyze_product(
    request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
    api_key: str = Depends(verify_extension_key)
):
    """Analyze a product with style matching."""
    result = await service.analyze_product(request)
    return result
```

---

## 5. Image Processing in Python

### Research Findings

For converting and compressing product images to WebP format for local storage.

### Recommended Library: Pillow

**Installation**:
```bash
pip install Pillow
```

**Why Pillow?**
- Pure Python, cross-platform
- Built-in WebP support
- Comprehensive image manipulation
- Active maintenance
- Part of Python imaging ecosystem

### Image Optimization Implementation

```python
# utils/image_processing.py
from PIL import Image
import io
from typing import Optional

async def convert_to_webp(
    image_data: bytes,
    max_size_kb: int = 200,
    quality: int = 85
) -> bytes:
    """
    Convert image to WebP format with size constraint.

    Args:
        image_data: Original image bytes
        max_size_kb: Maximum file size in KB
        quality: Initial quality (0-100)

    Returns:
        WebP image bytes under max_size_kb
    """
    # Open image
    img = Image.open(io.BytesIO(image_data))

    # Convert RGBA to RGB if necessary (WebP lossy doesn't support alpha)
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha as mask
        img = background

    # Start with high quality
    current_quality = quality
    output = io.BytesIO()

    # Iteratively reduce quality until under size limit
    while current_quality > 10:
        output.seek(0)
        output.truncate()

        img.save(output, format="WEBP", quality=current_quality)
        size_kb = len(output.getvalue()) / 1024

        if size_kb <= max_size_kb:
            break

        # Reduce quality by 5
        current_quality -= 5

    return output.getvalue()


async def resize_if_large(
    image_data: bytes,
    max_width: int = 1200,
    max_height: int = 1200
) -> bytes:
    """Resize image if it exceeds max dimensions."""
    img = Image.open(io.BytesIO(image_data))

    # Calculate new size maintaining aspect ratio
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format=img.format)
    return output.getvalue()


async def download_and_process_image(
    url: str,
    max_size_kb: int = 200
) -> bytes:
    """Download image from URL and convert to optimized WebP."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        image_data = response.content

    # Resize if needed
    image_data = await resize_if_large(image_data)

    # Convert to WebP
    webp_data = await convert_to_webp(image_data, max_size_kb)

    return webp_data
```

### Storage Strategy

**Option 1: Store in Database (Recommended for MVP)**
```python
# Store as BLOB in SQLite
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    image_data BLOB NOT NULL,
    file_size INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Option 2: Store as Files**
```python
import aiofiles
from pathlib import Path

async def save_image_file(
    image_data: bytes,
    product_id: int,
    image_index: int
) -> str:
    """Save image to filesystem."""
    images_dir = Path("storage/images")
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"product_{product_id}_{image_index}.webp"
    filepath = images_dir / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(image_data)

    return str(filepath)
```

---

## 6. Error Handling & Exception Middleware

### Best Practices

**Custom Exception Handler**:
```python
# core/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class StyleAssistantException(Exception):
    """Base exception for application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class CacheError(StyleAssistantException):
    """Database cache error."""
    pass

class AIProviderError(StyleAssistantException):
    """AI provider API error."""
    pass

# Exception handlers
@app.exception_handler(StyleAssistantException)
async def custom_exception_handler(
    request: Request,
    exc: StyleAssistantException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

---

## Key Recommendations

### Architecture Decisions

1. **Use Domain-Driven Structure**: Organize code by feature domain (analysis, products, costs) rather than by file type. This scales better and improves code locality.

2. **Use aiosqlite**: Despite the performance overhead, async SQLite is the right choice for FastAPI. The non-blocking behavior is more important than raw speed for our use case.

3. **Aggressive Prompt Caching**: Cache user profiles and analysis schemas to achieve 50%+ cost reduction. The 5-minute TTL is perfect for browsing sessions.

4. **Dependency Injection for Everything**: Database sessions, AI providers, services - all should use FastAPI's dependency injection for testability.

5. **Service Layer Pattern**: Keep routers thin. Business logic goes in service classes that can be tested independently.

### Implementation Priorities

**Phase 1: Core Infrastructure**
1. Set up FastAPI with domain-driven structure
2. Implement aiosqlite database layer with async sessions
3. Create AI provider abstraction with Claude implementation
4. Add prompt caching support
5. Build cost calculation utilities

**Phase 2: Feature Development**
1. Product extraction and storage
2. Analysis endpoint with cache checking
3. Cost tracking and aggregation
4. Error handling and logging

**Phase 3: Optimization**
1. Fine-tune prompt caching strategy
2. Add database indexes for common queries
3. Implement connection retry logic
4. Add comprehensive error messages

### Testing Strategy

1. **Unit Tests**: Service layer functions with mocked dependencies
2. **Integration Tests**: API endpoints with test database
3. **Cost Tests**: Verify prompt caching works as expected
4. **Load Tests**: Ensure async performance under concurrent requests

---

## Additional Resources

### Official Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **aiosqlite**: https://aiosqlite.omnilib.dev/
- **Anthropic Claude API**: https://docs.anthropic.com/
- **Claude Prompt Caching**: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- **Pillow**: https://pillow.readthedocs.io/

### Code Examples & Tutorials

- **FastAPI Best Practices**: https://github.com/zhanymkanov/fastapi-best-practices
- **Anthropic Cookbook**: https://github.com/anthropics/anthropic-cookbook
- **FastAPI Project Structure Guide**: https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f

### Cost Calculators

- **Claude API Cost Calculator**: https://calculatequick.com/ai/claude-token-cost-calculator/

---

## Conclusion

The research findings provide a solid foundation for implementing the Style Assistant backend:

1. **FastAPI** with domain-driven structure offers excellent scalability and maintainability
2. **aiosqlite** provides async SQLite access suitable for FastAPI despite slight performance overhead
3. **Claude prompt caching** can reduce costs by 50-90% when implemented correctly
4. **Dependency injection** patterns ensure testable, maintainable code
5. **Pillow** handles all image processing needs efficiently

The next step is to validate this architecture with the Architecture Validation Subagent, who will assess technical feasibility and identify potential issues before implementation begins.

---

**Research completed by**: Technical Research Subagent
**Date**: 2025-11-11
**Phase**: Research
**Status**: Ready for Architecture Validation

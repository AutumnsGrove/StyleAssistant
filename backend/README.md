# Backend

FastAPI backend for the GroveAssistant browser extension.

## Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── database.py             # SQLite database interface
├── models.py               # Pydantic models for API
├── utils.py                # Helper functions (cost calc, image processing)
├── ai_providers/           # AI provider abstraction
│   ├── base.py            # Abstract AIProvider class
│   └── claude.py          # Claude implementation
└── extractors/             # Product extractors
    ├── base.py            # Base extractor class
    └── uniqlo.py          # Uniqlo-specific extractor
```

## Database Schema

The SQLite database includes these tables:
- `user_profile` - User style profile from quiz
- `products` - Product cache with images
- `analyses` - AI analysis results cache
- `settings` - Extension settings
- `cost_log` - API cost tracking
- `debug_log` - Error and debug logging

See `GroveAssistantSpec.md` for complete schema details.

## API Endpoints

- `POST /api/analyze` - Analyze a product
- `POST /api/test-connection` - Test API key connection
- `GET /api/costs/session/{session_id}` - Get session costs
- `GET /api/costs/total` - Get all-time costs (TODO)

## Running

```bash
# Development mode with auto-reload
uv run uvicorn backend.main:app --reload

# Production mode
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Development

The database file will be created at `backend/grove_assistant.db` on first run.

# Tests

This directory contains all tests for the GroveAssistant project.

## Structure

```
tests/
├── conftest.py           # Shared pytest fixtures
├── backend/              # Backend API tests
│   ├── test_database.py
│   ├── test_api.py
│   ├── test_ai_providers.py
│   └── test_extractors.py
└── extension/            # Extension tests (future)
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run specific test file
uv run pytest tests/backend/test_database.py

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_cost"
```

## Writing Tests

- Use descriptive test names: `test_function_name_expected_behavior`
- Use fixtures from `conftest.py` for common test data
- Mock external API calls (Anthropic, etc.)
- Test both success and error cases
- Aim for high coverage (>80%)

## Fixtures

- `temp_db` - Temporary SQLite database for testing
- `mock_anthropic_response` - Mocked Claude API response
- `sample_product_data` - Sample product data
- `sample_user_profile` - Sample user profile

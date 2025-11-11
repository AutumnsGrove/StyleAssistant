# Development Guide

Quick reference for developing Style Assistant.

## Initial Setup (One-time)

```bash
# 1. Python dependencies (already done)
uv sync --all-extras

# 2. Extension dependencies
cd extension
npm install
cd ..

# 3. Configure secrets
cp secrets_template.json secrets.json
# Edit secrets.json and add your Anthropic API key
```

## Daily Development Workflow

### Backend Development

```bash
# Start the backend server
uv run uvicorn backend.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=backend --cov-report=html

# Format code
uv run black backend/ tests/

# Lint code
uv run ruff backend/ tests/
```

### Extension Development

```bash
cd extension

# Build TypeScript (one-time)
npm run build

# Watch mode (rebuilds on file changes)
npm run watch

# Lint
npm run lint

# Format
npm run format
```

### Loading Extension in Firefox

1. Build the extension: `cd extension && npm run build`
2. Open Firefox
3. Go to `about:debugging#/runtime/this-firefox`
4. Click "Load Temporary Add-on"
5. Select `extension/manifest.json`

## Project Structure

```
.
├── backend/                 # Python FastAPI backend
│   ├── main.py             # API entry point
│   ├── database.py         # SQLite interface
│   ├── models.py           # Pydantic models
│   ├── utils.py            # Helpers
│   ├── ai_providers/       # AI abstraction layer
│   └── extractors/         # Product extractors
│
├── extension/              # Firefox extension
│   ├── src/               # TypeScript source
│   ├── dist/              # Compiled JS (gitignored)
│   ├── manifest.json      # Extension manifest
│   └── *.html             # UI pages
│
├── tests/                 # Test suite
│   ├── conftest.py       # Shared fixtures
│   └── backend/          # Backend tests
│
└── secrets.json          # API keys (gitignored)
```

## Useful Commands

```bash
# Check Python version
uv run python --version

# Check installed packages
uv pip list

# Add new Python dependency
uv add package-name

# Add new dev dependency
uv add --dev package-name

# Run specific test
uv run pytest tests/backend/test_database.py -v

# Run tests matching pattern
uv run pytest -k "test_cost"

# TypeScript build
cd extension && npm run build

# TypeScript watch mode
cd extension && npm run watch
```

## Troubleshooting

### "Module not found" errors
```bash
uv sync
```

### TypeScript compilation errors
```bash
cd extension
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Extension not loading
1. Check `extension/dist/` exists and has compiled JS files
2. Rebuild: `cd extension && npm run build`
3. Check browser console for errors

### Database errors
- Delete `backend/style_assistant.db` to reset
- Check database schema in `backend/database.py`

## Code Style

- **Python**: Black (88 char line length), Ruff for linting
- **TypeScript**: Prettier (88 char line length), ESLint
- **Commits**: Conventional commits format (see CLAUDE.md)

## Testing Philosophy

- Write tests alongside implementation
- Aim for >80% coverage
- Test success and error cases
- Mock external APIs (Anthropic)
- Use fixtures from `tests/conftest.py`

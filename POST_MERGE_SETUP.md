# Post-Merge Setup Guide

This document covers manual setup steps that need to be completed after merging.

## 1. API Keys & Secrets

### Anthropic API Key

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Copy `secrets_template.json` to `secrets.json`:
   ```bash
   cp secrets_template.json secrets.json
   ```
3. Add your API key to `secrets.json`:
   ```json
   {
     "anthropic_api_key": "sk-ant-your-key-here"
   }
   ```

**Important:** Never commit `secrets.json` - it's already in `.gitignore`.

### Environment Variables (Alternative)

Instead of `secrets.json`, you can use environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

## 2. Backend Setup

### Install Dependencies

```bash
# Using UV package manager (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Run the Backend

```bash
# Development server with auto-reload
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Or production mode
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Verify Backend

```bash
# Health check
curl http://localhost:8000/health

# Test AI connection (requires API key)
curl http://localhost:8000/api/test-connection
```

## 3. Extension Setup

### Build Extension

```bash
cd extension
npm install
npm run build
```

### Load in Firefox

1. Open Firefox and navigate to `about:debugging`
2. Click "This Firefox" in the sidebar
3. Click "Load Temporary Add-on"
4. Navigate to `extension/` and select `manifest.json`

### Configure Extension

1. Click the GroveAssistant icon in the toolbar
2. Verify "Backend: Connected" status
3. (Optional) Take the Style Quiz for personalized recommendations

## 4. Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=backend --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 5. Development Workflow

### Backend Development

```bash
# Start backend in development mode
uv run uvicorn backend.main:app --reload

# Watch for Python changes and run tests
uv run pytest tests/ -v --tb=short
```

### Extension Development

```bash
cd extension

# Watch for TypeScript changes
npm run watch

# In Firefox, reload the extension after changes
```

## 6. Database

The SQLite database is created automatically at `backend/grove_assistant.db` when the backend starts.

To reset the database:
```bash
rm backend/grove_assistant.db
# Restart the backend
```

## 7. Optional: Cloudflare Workers Deployment

If deploying to Cloudflare Workers:

1. Install Wrangler: `npm install -g wrangler`
2. Login: `wrangler login`
3. Configure `wrangler.toml` (create from template)
4. Set secrets: `wrangler secret put ANTHROPIC_API_KEY`
5. Deploy: `wrangler deploy`

*Note: Workers deployment requires additional configuration not covered here.*

## Troubleshooting

### "API key not configured" Error

- Verify `secrets.json` exists and contains valid key
- Check that the key starts with `sk-ant-`
- Try setting as environment variable instead

### Extension Not Loading

- Ensure TypeScript compiled: `npm run build`
- Check browser console for errors
- Verify `dist/` directory was created

### Backend Connection Failed

- Verify backend is running on correct port
- Check CORS settings if using different origins
- Ensure firewall allows localhost:8000

---

For more details, see:
- `CLAUDE.md` - Project instructions
- `GroveAssistantSpec.md` - Full specification
- `AgentUsage/` - Developer guides

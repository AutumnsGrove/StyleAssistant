# GroveAssistant - AI-Powered Fashion Browser Extension

A Firefox browser extension that provides personalized style analysis and outfit suggestions for clothing products on e-commerce sites using Claude AI.

**Features:** Personalized style quiz | AI-powered outfit matching | Cost-optimized Claude API usage | Product caching | Real-time analysis

## Quick Start

### Prerequisites
- Python 3.11+ with UV package manager
- Node.js 18+ (for extension development)
- Firefox Developer Edition (recommended) or Firefox
- Anthropic API key for Claude

### Backend Setup

```bash
# Install Python dependencies
uv sync --all-extras

# Create secrets file
cp secrets_template.json secrets.json
# Edit secrets.json and add your Anthropic API key

# Run the backend
uv run uvicorn backend.main:app --reload
```

### Extension Setup

```bash
# Navigate to extension directory
cd extension

# Install dependencies
npm install

# Build TypeScript
npm run build

# Load extension in Firefox
# 1. Open Firefox
# 2. Navigate to about:debugging#/runtime/this-firefox
# 3. Click "Load Temporary Add-on"
# 4. Select manifest.json from the extension/ directory
```

### Running the Project

1. Start the FastAPI backend: `uv run uvicorn backend.main:app --reload`
2. Load the extension in Firefox (see above)
3. Navigate to a Uniqlo product page
4. Take the style quiz via the extension popup
5. See personalized analysis appear on product pages!

---

## Project Structure

```
grove-assistant/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI app entry point
│   ├── database.py            # SQLite connection & queries
│   ├── config.py              # Pydantic settings
│   ├── ai_providers/          # AI provider abstraction
│   │   ├── base.py           # Abstract AIProvider class
│   │   ├── claude.py         # Claude implementation
│   │   └── prompts.py        # AI prompts
│   ├── extractors/            # Product extractors
│   │   ├── base.py           # Base extractor
│   │   └── uniqlo.py         # Uniqlo-specific extractor
│   ├── costs/                 # Cost tracking
│   └── core/                  # Core utilities
│
├── extension/                  # Firefox extension
│   ├── manifest.json          # Extension manifest
│   ├── src/                   # TypeScript source
│   └── package.json           # Node dependencies
│
├── tests/                     # Test suite
│   └── conftest.py           # Shared fixtures
│
├── CLAUDE.md                  # Project instructions for Claude Code
├── AgentUsage/                # Agent workflow guides
├── GroveAssistantSpec.md      # Complete project specification
└── TODOS.md                   # Development milestones
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Firefox WebExtension (Manifest V3) |
| Backend | FastAPI (Python) |
| Database | SQLite (async via aiosqlite) |
| AI | Claude API (Sonnet 4.5 + Haiku 4.5) |
| Image Processing | Pillow (WebP conversion) |
| Package Manager | UV (Python), npm (Extension) |

---

## Key Features

### Personalized Style Analysis
- **Interactive Style Quiz** - Multi-select questions covering fit preferences, color palettes, formality spectrum, gender presentation, aesthetics, and priorities
- **Style Match Scoring** - 0-100% match score with color-coded indicators (excellent, good, moderate, poor)
- **Context-Aware Suggestions** - Outfit pairings specific to your style profile and the product being viewed
- **Attribute Analysis** - Warmth, formality, vibe, comfort, and versatility ratings

### Cost-Optimized AI
- **Smart Caching** - User profile and extraction schema cached via Claude prompt caching
- **Dual-Mode Operation** - Full analysis with Sonnet 4.5 vs. basic analysis with Haiku 4.5
- **Cost Tracking** - Per-session and all-time tracking with detailed breakdowns
- **Product Cache** - SQLite stores analyzed products to avoid redundant API calls

### Smart Product Detection
- **Automatic Page Detection** - Identifies Uniqlo product pages via URL patterns and DOM validation
- **Comprehensive Extraction** - Title, price, materials, colors, sizes, images, and descriptions
- **Image Optimization** - WebP conversion and compression to ~200KB per image
- **Multi-Site Ready** - Extensible architecture for adding more e-commerce sites

---

## Documentation

| Guide | Description |
|-------|-------------|
| `AgentUsage/README.md` | Master index of all documentation |
| `AgentUsage/git_guide.md` | Git workflow and conventional commits |
| `AgentUsage/secrets_management.md` | API key security |
| `AgentUsage/uv_usage.md` | UV package manager |
| `AgentUsage/testing_strategies.md` | Test organization |
| `GroveAssistantSpec.md` | Full product specification |

---

## Development

```bash
# Run backend with auto-reload
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

---

## Security

- `secrets.json` in `.gitignore`
- Pre-commit secrets scanner available
- Environment variable fallback patterns
- See `AgentUsage/secrets_management.md` for details

---

## Working with Claude Code

This project is optimized for Claude Code CLI:

- **CLAUDE.md** triggers automatic context loading
- **Structured guides** in AgentUsage/ for quick reference
- **Git commit standards** with auto-formatting

---

**Last updated:** 2025-12-01
**Maintained for:** Claude Code CLI

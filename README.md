# Style Assistant - AI-Powered Fashion Browser Extension

A Firefox browser extension that provides personalized style analysis and outfit suggestions for clothing products on e-commerce sites using Claude AI.

**Features:** Personalized style quiz • AI-powered outfit matching • Cost-optimized Claude API usage • Product caching • Real-time analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with UV package manager
- Node.js 18+ (for extension development)
- Firefox Developer Edition (recommended) or Firefox
- Anthropic API key for Claude

### Backend Setup

```bash
# Install Python dependencies
uv init
uv add fastapi uvicorn anthropic pillow

# Create secrets file
cp ClaudeUsage/templates/secrets_template.json secrets.json
# Edit secrets.json and add your Anthropic API key

# Run the backend
uv run uvicorn backend.main:app --reload
```

### Extension Setup

```bash
# Navigate to extension directory
cd extension

# Install dependencies (if using npm for build tools)
npm install

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

## 📁 Project Structure

```
style-assistant/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI app
│   ├── database.py            # SQLite connection & queries
│   ├── models.py              # Pydantic models
│   ├── ai_providers/          # AI provider abstraction
│   │   ├── base.py           # Abstract AIProvider class
│   │   └── claude.py         # Claude implementation
│   ├── extractors/            # Product extractors
│   │   ├── base.py           # Base extractor
│   │   └── uniqlo.py         # Uniqlo-specific extractor
│   └── utils.py              # Helpers, cost calc, image processing
│
├── extension/                  # Firefox extension
│   ├── manifest.json          # Extension manifest
│   ├── background.js          # Background service worker
│   ├── content/               # Content scripts
│   │   ├── content.js        # Main content script
│   │   ├── injector.js       # DOM injection logic
│   │   └── styles.css        # Analysis box styles
│   ├── popup/                 # Extension popup
│   │   ├── popup.html
│   │   ├── popup.js
│   │   └── popup.css
│   ├── quiz/                  # Style quiz
│   │   ├── quiz.html
│   │   ├── quiz.js
│   │   └── quiz.css
│   └── storage.js            # Extension storage wrapper
│
├── CLAUDE.md                  # Project instructions for Claude Code
├── ClaudeUsage/               # Claude Code workflow guides
└── StyleAssistantSpec.md      # Complete project specification
```

---

## 🏠 House Agents Integration

This template works seamlessly with [house-agents](https://github.com/houseworthe/house-agents) - specialized Claude Code sub-agents that keep your context clean.

### What Are House Agents?

Specialized sub-agents that run heavy operations in separate context windows:
- **house-research** - Search 70k+ tokens across files, return 3k summary (95% savings)
- **house-git** - Analyze 43k token diffs, return 500 token summary (98% savings)
- **house-bash** - Process 21k+ command output, return 700 token summary (97% savings)

### Quick Install

**Project-Level (this project only):**
```bash
git clone https://github.com/houseworthe/house-agents.git /tmp/house-agents
cp -r /tmp/house-agents/.claude .
```

**User-Wide (all projects):**
```bash
git clone https://github.com/houseworthe/house-agents.git /tmp/house-agents
mkdir -p ~/.claude/agents
cp /tmp/house-agents/.claude/agents/*.md ~/.claude/agents/
```

**Test Installation:**
```
Use house-research to find all TODO comments in the codebase
```

See [ClaudeUsage/house_agents.md](ClaudeUsage/house_agents.md) for usage patterns and examples.

**Credit:** House Agents by [@houseworthe](https://github.com/houseworthe/house-agents) (v0.2.0-beta)

---

## 🎯 Key Features

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

### Seamless UX
- **Non-Intrusive UI** - Collapsed by default, expands on click
- **DOM Injection** - Integrates naturally into product pages with fallback overlay
- **Real-Time Analysis** - Immediate feedback as you browse
- **Debug Logging** - Comprehensive error tracking and user-friendly messages

---

## 📚 Documentation Structure

All guides follow a consistent, scannable format:

1. **Overview** - What the guide covers
2. **When to Use** - Specific triggers and scenarios
3. **Core Concepts** - Key principles
4. **Practical Examples** - Real-world code
5. **Common Pitfalls** - What to avoid
6. **Related Guides** - Cross-references

See [ClaudeUsage/README.md](ClaudeUsage/README.md) for the complete index.

---

<!-- TEMPLATE: START -->

## 🛠️ Customization Workflow

After running setup:

1. **Edit CLAUDE.md** - Fill in your project specifics
   - Project purpose
   - Tech stack
   - Architecture notes

2. **Create secrets files** (if needed)
   ```bash
   # For Python projects
   cp ClaudeUsage/templates/secrets_template.json secrets_template.json
   cp secrets_template.json secrets.json
   # Edit secrets.json with real API keys
   ```

3. **Set up dependencies**
   ```bash
   # Python with UV
   uv init

   # JavaScript/Node
   npm init -y

   # Go
   go mod init yourproject
   ```

4. **Install git hooks** (recommended)
   ```bash
   # Interactive installer (auto-detects your language)
   ./ClaudeUsage/pre_commit_hooks/install_hooks.sh

   # This installs:
   # - Code quality checks (formatters + linters)
   # - Security scanner (prevents API key leaks)
   # - Test runner (blocks push if tests fail)
   # - Dependency auto-updater
   ```

5. **Update TODOS.md** - Add your specific tasks

<!-- TEMPLATE: END -->

---

## 💡 Key Workflows

### Starting a New Feature
1. Check `TODOS.md` for pending tasks
2. Use Context7 to fetch relevant library docs
3. Follow git workflow for commits
4. Update TODOS.md as you progress

### Managing Secrets
1. Read `ClaudeUsage/secrets_management.md`
2. Create `secrets.json` (gitignored)
3. Provide `secrets_template.json` for team
4. Use environment variable fallbacks

### Large Codebase Search
1. Use house-research agent for 20+ file searches
2. Check `ClaudeUsage/house_agents.md` for patterns
3. Use subagents for complex multi-step tasks

### Writing Tests
1. Review `ClaudeUsage/testing_strategies.md`
2. Follow framework-specific patterns
3. Use test-strategist agent for planning

---

## 🔐 Security Defaults

This template includes security best practices by default:

- ✅ `secrets.json` in `.gitignore`
- ✅ **Pre-commit secrets scanner** - Detects 15+ secret patterns before commit
  - Anthropic, OpenAI, AWS, GitHub, Google API keys
  - JWT tokens, bearer tokens, private keys
  - Hardcoded passwords and database credentials
  - Actionable fix instructions when secrets detected
- ✅ Environment variable fallback patterns
- ✅ Security audit guides in `secrets_advanced.md`

---

## 🤝 Working with Claude Code

This template is optimized for Claude Code CLI. Key features:

- **CLAUDE.md** triggers automatic context loading
- **Structured guides** for quick reference without token bloat
- **Subagent workflows** for complex tasks
- **Git commit standards** with auto-formatting

### Example Session
```bash
cd ~/Projects/MyNewProject/

# Claude automatically reads CLAUDE.md and knows your project context
claude "Add user authentication with JWT tokens"

# Claude will:
# 1. Check TODOS.md
# 2. Use Context7 to fetch JWT library docs
# 3. Implement following your git commit standards
# 4. Update TODOS.md
# 5. Commit with proper message format
```

---

## 📖 Learning Path

Recommended reading order for new projects:

1. [project_structure.md](ClaudeUsage/project_structure.md) - Directory layouts
2. [git_guide.md](ClaudeUsage/git_guide.md) - Version control and conventional commits
3. [db_usage.md](ClaudeUsage/db_usage.md) - Database setup (if using databases)
4. [secrets_management.md](ClaudeUsage/secrets_management.md) - API keys
5. [uv_usage.md](ClaudeUsage/uv_usage.md) - Python dependencies (if applicable)
6. [testing_strategies.md](ClaudeUsage/testing_strategies.md) - Test setup
7. [house_agents.md](ClaudeUsage/house_agents.md) - Advanced workflows

---

## 🆘 Troubleshooting

<!-- TEMPLATE: START -->

### "Git not initialized"
```bash
git init
git add .
git commit -m "Initial commit"
```

### "CLAUDE.md not found"
If you see this error, the setup script may not have run properly. Make sure you've run `bash setup.sh` in your project directory.

<!-- TEMPLATE: END -->

### "Pre-commit hooks not working"
```bash
chmod +x ClaudeUsage/pre_commit_hooks/*
./ClaudeUsage/pre_commit_hooks/install_hooks.sh
```

See [ClaudeUsage/pre_commit_hooks/TROUBLESHOOTING.md](ClaudeUsage/pre_commit_hooks/TROUBLESHOOTING.md) for comprehensive hook troubleshooting.

---

<!-- TEMPLATE: START -->

## 🔄 Keeping BaseProject Updated

To get updates from BaseProject while preserving your customizations:

```bash
# In your project directory
# Option 1: Manual merge of specific guides
cp /path/to/BaseProject/ClaudeUsage/new_guide.md ClaudeUsage/

# Option 2: Update all guides (careful - review diffs first)
rsync -av --exclude='CLAUDE.md' /path/to/BaseProject/ClaudeUsage/ ClaudeUsage/

# Review changes
git diff

# Commit updates
git add ClaudeUsage/
git commit -m "Update ClaudeUsage guides from BaseProject"
```

## 🎉 What's Next?

After setup:

1. **Customize** - Edit CLAUDE.md with your project details
2. **Explore** - Read guides in ClaudeUsage/ directory
3. **Build** - Start coding with Claude Code
4. **Iterate** - Update TODOS.md and guides as needed

<!-- TEMPLATE: END -->

---

## 📝 Contributing

Found a better pattern? Want to add a guide?

This template uses a **two-branch strategy**:
- **`main` branch** - Clean, user-facing template (you're here)
- **`dev` branch** - Template development and maintenance

### For Template Development:
1. Check out the [dev branch](https://github.com/AutumnsGrove/BaseProject/tree/dev)
2. Read [CONTRIBUTING.md](https://github.com/AutumnsGrove/BaseProject/blob/dev/CONTRIBUTING.md) for full workflow
3. Make changes in dev branch
4. Test thoroughly before merging to main

### For Quick Improvements:
1. Add your guide to `ClaudeUsage/`
2. Update `ClaudeUsage/README.md` index
3. Follow the documentation standards in `ClaudeUsage/documentation_standards.md`
4. Commit with proper message format

---

## 📄 License

This template is provided as-is for use with Claude Code. Customize freely for your projects.

---

**Last updated:** 2025-10-19
**Maintained for:** Claude Code CLI
**Guides:** 16 comprehensive workflow documents

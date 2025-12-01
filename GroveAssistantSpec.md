---
aliases: 
date created: Tuesday, November 11th 2025, 11:36:14 am
date modified: Tuesday, November 11th 2025, 11:36:28 am
tags: 
type:
---

# Project Spec: GroveAssistant Browser Extension

## Overview

A Firefox browser extension that provides personalized style analysis and outfit suggestions for clothing products on e-commerce sites (starting with Uniqlo). Uses Claude AI models for analysis with prompt caching optimization, tracks API costs, and offers both personalized and basic modes.

---

## Tech Stack

### Frontend

- **Extension**: Firefox WebExtension (Manifest V3)
- **Language**: JavaScript/TypeScript
- **UI Framework**: Vanilla JS (keep it lightweight)
- **Storage**: Firefox extension storage API + SQLite (via extension)

### Backend

- **Framework**: FastAPI (Python)
- **Database**: SQLite
- **AI Models**:
    - Claude Sonnet 4.5 (complex analysis, outfit suggestions)
    - Claude Haiku 4.5 (basic analysis, summaries)
    - Abstraction layer for future model support (LM Studio, Ollama, OpenRouter, OpenAI)
- **Deployment**: Local (localhost) for MVP
    - TODO: Cloudflare Workers deployment option

### AI Provider Architecture

```python
# Abstract base class for all AI providers
class AIProvider:
    def analyze_product(self, product_data, user_profile)
    def generate_outfit_suggestions(self, product_data, user_profile)
    def basic_analysis(self, product_data)

# Implementations
class ClaudeProvider(AIProvider)  # Primary
class LMStudioProvider(AIProvider)  # TODO
class OpenRouterProvider(AIProvider)  # TODO
class OpenAIProvider(AIProvider)  # TODO
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Firefox Extension                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Popup UI   │  │Content Script│  │  Background  │ │
│  │  (Settings,  │  │ (Product Page│  │   Worker     │ │
│  │   Quiz,      │  │  Injection)  │  │ (API Calls)  │ │
│  │   Costs)     │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Local)                 │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ AI Provider  │  │   Product    │  │   Cost       │ │
│  │  Abstraction │  │  Extractor   │  │  Tracker     │ │
│  │    Layer     │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              SQLite Database                      │  │
│  │  - user_profile  - products  - analyses          │  │
│  │  - settings      - cost_log  - debug_log         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### SQLite Tables

```sql
-- User style profile (from quiz)
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
    site TEXT NOT NULL,  -- 'uniqlo' for now
    title TEXT,
    price REAL,
    currency TEXT,
    description TEXT,
    materials TEXT,
    category TEXT,
    colors TEXT,  -- JSON array
    sizes TEXT,   -- JSON array
    image_paths TEXT,  -- JSON array of local WebP paths
    raw_data TEXT,  -- JSON blob of full extracted data
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis cache
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    profile_version TEXT NOT NULL,  -- Hash of user_profile to detect changes
    model_used TEXT NOT NULL,  -- 'sonnet-4.5' or 'haiku-4.5'
    analysis_type TEXT NOT NULL,  -- 'full', 'basic', 'outfit'
    analysis_data TEXT NOT NULL,  -- JSON blob
    tokens_used INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
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
    session_id TEXT,  -- UUID for current session
    model TEXT NOT NULL,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    cost_usd REAL,
    cached_tokens INTEGER DEFAULT 0,  -- For Claude caching
    request_type TEXT,  -- 'analysis', 'outfit', 'basic'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Debug log
CREATE TABLE debug_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,  -- 'info', 'warning', 'error'
    component TEXT,  -- 'content_script', 'background', 'api', etc.
    message TEXT NOT NULL,
    stack_trace TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### JSON Schema Examples

**user_profile.profile_data:**

```json
{
  "quiz_version": "1.0",
  "fit_preferences": ["oversized", "relaxed"],
  "color_palette": ["black", "white", "earth_tones", "pastels"],
  "formality_range": [1, 5],  // 1=casual, 10=formal
  "gender_presentation": ["feminine", "androgynous"],
  "aesthetics": ["minimalist", "cottagecore", "comfortable"],
  "priorities": ["comfort", "warmth", "pockets", "versatility"],
  "avoid": ["tight_fit", "crop_tops", "bright_colors"],
  "style_keywords": ["cozy", "nature-inspired", "practical"]
}
```

**analyses.analysis_data:**

```json
{
  "style_match_score": 85,  // 0-100
  "match_reasons": ["Oversized fit matches preference", "Earth tone colors"],
  "mismatch_reasons": ["Slightly more formal than usual style"],
  "attributes": {
    "warmth": "medium",
    "formality": "casual-smart",
    "vibe": "cozy minimalist",
    "comfort": "high",
    "versatility": "high"
  },
  "pairing_suggestions": [
    {"category": "bottoms", "suggestion": "black straight-leg jeans"},
    {"category": "shoes", "suggestion": "white sneakers or ankle boots"},
    {"category": "accessories", "suggestion": "minimal gold jewelry"}
  ],
  "color_analysis": "Warm beige works well with your earth tone palette",
  "season_fit": ["fall", "spring"],
  "occasion_tags": ["everyday", "casual_outing", "coffee_shop"]
}
```

---

## Feature Requirements

### 1. Style Quiz

**Location**: Opens in new tab on first install, accessible via popup menu

**Questions** (presented with visual examples):

1. **Fit Preferences** (multi-select):
    - Oversized / Relaxed / Regular / Fitted / Tailored
2. **Color Palette** (multi-select):
    - Neutrals (black/white/gray)
    - Earth tones (brown/beige/olive)
    - Pastels
    - Jewel tones
    - Bright colors
    - All black everything
3. **Formality Spectrum** (slider 1-10):
    - 1-3: Casual (loungewear, streetwear)
    - 4-6: Smart casual
    - 7-10: Business/formal
4. **Gender Presentation** (multi-select):
    - Masculine / Feminine / Androgynous / Fluid
5. **Aesthetic Categories** (multi-select, with image examples):
    - Minimalist / Streetwear / Cottagecore / Dark academia
    - Bohemian / Sporty / Grunge / Preppy / Y2K
6. **Priority Features** (rank top 3):
    - Comfort / Warmth / Pockets / Versatility
    - Durability / Unique design / Affordability
7. **What to Avoid** (multi-select):
    - Tight fit / Crop tops / Bright patterns
    - Synthetic materials / High maintenance care

**Output**: Structured JSON stored in `user_profile` table

**Quiz Retake**: Accessible anytime via popup → "Retake Style Quiz" button

---

### 2. Product Page Detection & Extraction

**Target Site**: Uniqlo (MVP)

**Detection Method**:

- URL pattern matching: `/products/` or similar
- DOM structure validation (check for product title, price, images)

**Universal Extraction Pattern**:

```javascript
{
  title: string,
  price: number,
  currency: string,
  description: string,
  materials: string,
  category: string,
  colors: string[],
  sizes: string[],
  images: string[],  // URLs
  url: string,
  site: 'uniqlo'
}
```

**Image Processing**:

- Download product images
- Convert to WebP
- Compress to ~200KB max per image
- Store locally in extension storage
- Save file paths in DB

**Extraction Flow**:

1. Content script detects product page
2. Extracts data using CSS selectors (site-specific config)
3. Sends to background worker
4. Background worker forwards to FastAPI backend
5. Backend processes, stores in DB, returns analysis

---

### 3. Analysis Box UI

**Placement**:

- **Primary**: DOM injection above product title (match width)
- **Fallback**: Floating overlay positioned above title

**Collapsed State** (Default):

```
┌────────────────────────────────────┐
│ ⭐ 85% Style Match      ▼ Expand  │
└────────────────────────────────────┘
```

- Match score (0-100%)
- Star icon with color coding:
    - 🟢 Green: 80-100% (excellent match)
    - 🟡 Yellow: 60-79% (good match)
    - 🟠 Orange: 40-59% (moderate match)
    - 🔴 Red: 0-39% (poor match)
- Down arrow to expand
- Height: ~40px
- Subtle shadow, rounded corners

**Expanded State**:

```
┌─────────────────────────────────────────────────┐
│ ⭐ 85% Style Match                    ▲ Collapse │
├─────────────────────────────────────────────────┤
│ 🎯 Why This Works:                               │
│  • Oversized fit matches your preference        │
│  • Earth tone colors align with your palette    │
│                                                  │
│ ⚠️ Considerations:                               │
│  • Slightly more formal than your usual style   │
│                                                  │
│ 📋 Key Attributes:                               │
│  Warmth: ●●●○○  Formality: Casual-Smart        │
│  Vibe: Cozy Minimalist                          │
│                                                  │
│ 👕 Pairs Well With:                              │
│  • Black straight-leg jeans                     │
│  • White sneakers or ankle boots                │
│  • Minimal gold jewelry                         │
│                                                  │
│ 💬 Color Analysis:                               │
│  "Warm beige works well with your earth tone    │
│   palette and can be dressed up or down."       │
│                                                  │
│ 🏷️ Best For:                                     │
│  Everyday wear • Casual outings • Coffee shops  │
├─────────────────────────────────────────────────┤
│ Analysis cost: $0.03                            │
└─────────────────────────────────────────────────┘
```

**Basic Mode** (No quiz completed):

```
┌─────────────────────────────────────────────────┐
│ 📋 Product Analysis              ▲ Collapse     │
├─────────────────────────────────────────────────┤
│ 📋 Key Attributes:                               │
│  Warmth: ●●●○○  Formality: Casual-Smart        │
│                                                  │
│ 👕 Suggested Pairings:                           │
│  • Dark jeans                                   │
│  • Light-colored shoes                          │
│  • Neutral accessories                          │
│                                                  │
│ ℹ️ Take the Style Quiz for personalized matches! │
│    [Take Quiz] button                           │
├─────────────────────────────────────────────────┤
│ Analysis cost: $0.01                            │
└─────────────────────────────────────────────────┘
```

**Box Behavior**:

- Show on EVERY product page (even poor matches)
- Default: Collapsed
- Setting: Toggle auto-expand
- Animate expand/collapse smoothly
- Non-intrusive styling (matches site theme where possible)

---

### 4. Extension Popup

**Layout**:

```
┌────────────────────────────────┐
│  GroveAssistant              │
├────────────────────────────────┤
│ 🔌 Extension Status            │
│  [Toggle ON/OFF]               │
│                                │
│ 🧠 Mode                         │
│  [ ] Basic Mode (Haiku only)   │
│                                │
│ 📊 Match Threshold             │
│  [=====>….] 60%              │
│  (Minimum score to highlight)  │
│                                │
│ 📦 Box Behavior                │
│  [ ] Auto-expand on page load  │
│                                │
│ 🎨 [Retake Style Quiz]         │
│                                │
├────────────────────────────────┤
│ 💰 Total Costs                  │
│  Session: $1.23                │
│  All-time: $45.67 (TODO)       │
│                                │
│ 🔑 API Settings                │
│  API Key: [••••••••] [Edit]    │
│  [Test Connection]             │
│                                │
│ 🐛 [View Debug Logs]           │
└────────────────────────────────┘
```

**Settings**:

- Master on/off toggle
- Basic mode checkbox (Haiku only)
- Match threshold slider (0-100%, default 60%)
- Auto-expand toggle
- API key input (masked)
- Connection test button
- Link to quiz page
- Cost tracking display
- Debug log access

---

### 5. AI Analysis System

**Claude Prompt Caching Strategy**:

- Cache user profile JSON (changes rarely)
- Cache product extraction schema/instructions
- Dynamic: product data, analysis request

**Model Selection**:

- **Haiku 4.5**:
    - Basic mode analysis
    - Product data summarization (if too long)
    - Quick attribute extraction
- **Sonnet 4.5**:
    - Full personalized analysis
    - Outfit pairing suggestions
    - Complex reasoning about style matches

**API Endpoints**:

```python
# FastAPI routes
POST /api/analyze
{
  "product_data": {…},
  "user_profile": {…} | null,
  "mode": "full" | "basic",
  "use_cache": true
}
→ Returns analysis_data JSON + cost info

POST /api/test-connection
{
  "api_key": "…"
}
→ Returns {"status": "ok"} or error

GET /api/costs/session/{session_id}
→ Returns session cost breakdown

GET /api/costs/total  (TODO)
→ Returns all-time costs
```

**Caching Logic**:

1. Check if product exists in DB
2. Check if analysis exists for current profile version
3. If cache hit: return immediately (free)
4. If cache miss: call Claude API with caching headers
5. Store analysis + cost in DB
6. Return to extension

**Error Handling**:

- API key missing: Show popup notification
- Claude API down: Display graceful error in box
- Rate limit hit: Show wait message with retry timer
- Invalid response: Log error, show generic message

---

### 6. Cost Tracking

**Session Tracking**:

- Generate UUID on extension load
- Track all API calls in `cost_log` table
- Calculate costs:
    
    ```python
    # Claude pricing (as of 2025)SONNET_INPUT = 0.003 / 1000   # per tokenSONNET_OUTPUT = 0.015 / 1000HAIKU_INPUT = 0.00025 / 1000HAIKU_OUTPUT = 0.00125 / 1000CACHED_INPUT = 0.0003 / 1000  # 10% of regular
    ```
    

**Display Locations**:

1. **Per-Analysis**: Bottom of expanded box
2. **Session Total**: Extension popup
3. **All-Time Total**: Extension popup (TODO)

**Popup Display**:

```
💰 Total Costs
Session: $1.23
  ├─ 3 full analyses: $0.89
  ├─ 5 basic analyses: $0.24
  └─ Cached savings: $0.10
  
All-time: $45.67 (TODO)
```

---

### 7. Logging & Debugging

**Debug Log Features**:

- All errors logged to `debug_log` table
- Viewable in popup → Debug Logs page
- Includes:
    - Timestamp
    - Component (content script, background, API)
    - Level (info, warning, error)
    - Message
    - Stack trace (if error)

**Never Crash**:

- Wrap all critical functions in try-catch
- Log errors gracefully
- Show user-friendly messages
- Continue operation where possible

**Log Retention**:

- Keep last 1000 entries
- Auto-cleanup older entries
- Export functionality for bug reports

---

## Implementation Phases

### Phase 1: Core Infrastructure

- [ ] FastAPI backend setup
- [ ] SQLite database schema
- [ ] AI provider abstraction layer
- [ ] Claude API integration with caching
- [ ] Basic product extraction (Uniqlo)
- [ ] Cost tracking system

### Phase 2: Extension Foundation

- [ ] Firefox extension manifest
- [ ] Content script injection (DOM + fallback)
- [ ] Background worker (API communication)
- [ ] Extension popup UI
- [ ] Settings storage

### Phase 3: Style Quiz

- [ ] Quiz page UI
- [ ] Question flow
- [ ] Profile generation
- [ ] Storage in DB

### Phase 4: Analysis & Display

- [ ] Product page detection
- [ ] Analysis box UI (collapsed/expanded)
- [ ] Full vs basic mode analysis
- [ ] Pairing suggestions

### Phase 5: Polish

- [ ] Error handling everywhere
- [ ] Debug logging system
- [ ] Cost display in all locations
- [ ] Performance optimization

---

## TODO List (Future Features)

### High Priority

- [ ] Persistent cost tracking (all-time totals)
- [ ] Multi-device sync via passphrase/token system
- [ ] Price history tracking with historical scraping
- [ ] Cloudflare Workers deployment option

### Medium Priority

- [ ] LM Studio local AI support
- [ ] OpenRouter multi-model support
- [ ] OpenAI GPT integration
- [ ] Implicit feedback learning (track likes/dislikes)
- [ ] More detailed outfit suggestions with specific products
- [ ] Support for additional clothing sites

### Low Priority

- [ ] Export style profile
- [ ] Share analyses with friends
- [ ] Wardrobe inventory integration
- [ ] Seasonal trend analysis

---

## File Structure

```
grove-assistant/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── database.py             # SQLite connection & queries
│   ├── models.py               # Pydantic models
│   ├── ai_providers/
│   │   ├── base.py            # Abstract AIProvider class
│   │   ├── claude.py          # ClaudeProvider implementation
│   │   └── (future providers)
│   ├── extractors/
│   │   ├── base.py            # Base extractor
│   │   └── uniqlo.py          # Uniqlo-specific extractor
│   ├── utils.py               # Helpers, cost calc, image processing
│   └── requirements.txt
│
├── extension/
│   ├── manifest.json
│   ├── background.js          # Background service worker
│   ├── content/
│   │   ├── content.js         # Content script
│   │   ├── injector.js        # DOM injection logic
│   │   └── styles.css         # Analysis box styles
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.js
│   │   └── popup.css
│   ├── quiz/
│   │   ├── quiz.html
│   │   ├── quiz.js
│   │   └── quiz.css
│   ├── icons/
│   │   └── (extension icons)
│   └── storage.js             # Extension storage wrapper
│
└── README.md
```

---

## Error States & Messages

**No API Key**:

> "⚠️ API key required. Click the extension icon to add your Claude API key."

**Claude API Down**:

> "🔌 Unable to connect to analysis service. Please try again in a moment."

**Rate Limited**:

> "⏱️ Rate limit reached. Retrying in 60 seconds…"

**Invalid Product Page**:

> "ℹ️ This doesn't appear to be a product page we can analyze."

**Basic Mode (No Quiz)**:

> "ℹ️ Take the Style Quiz for personalized matches! [Take Quiz]"

**Cache Hit** (optional subtle indicator):

> "💾 Cached analysis (free)"

---

## Success Criteria

✅ **Extension loads without crashing**  
✅ **Detects Uniqlo product pages correctly**  
✅ **Injects analysis box in correct position**  
✅ **Displays personalized analysis based on quiz**  
✅ **Falls back to basic mode gracefully**  
✅ **Tracks costs accurately per-session**  
✅ **All errors logged and handled**  
✅ **Claude caching reduces costs by ~50%+**  
✅ **Settings persist across sessions**  
✅ **Quiz results stored and applied correctly**

---

## Notes for Implementation

1. **Keep it simple first**: Get basic product extraction + one analysis working before adding complexity
2. **Test caching early**: This is critical for cost control
3. **DOM injection fallback**: Build both methods from the start
4. **Graceful degradation**: App should never crash, even if things go wrong
5. **Modular code**: Make AI provider swap easy for future
6. **Image optimization**: Don't let local storage bloat
7. **Security**: Never log API keys, sanitize all inputs

# GroveAssistant - Development TODOs

## Current Focus: V1 MVP ✅ COMPLETE

All 11 phases of the MVP have been completed. The extension is ready for testing.

### Phase 1: Infrastructure (Milestone 1) ✅
- [x] Set up FastAPI project structure
- [x] Configure UV package manager and dependencies
- [x] Set up SQLite database schema
- [x] Configure Pydantic settings for configuration
- [x] Implement error handling middleware
- [x] Create health check endpoint (`/health`)

### Phase 2: AI Provider System ✅
- [x] Implement abstract `AIProvider` base class
- [x] Create `ClaudeProvider` with Sonnet 4.5 & Haiku 4.5
- [x] Implement 3-breakpoint prompt caching (50-70% savings)
- [x] Add token counting and cost calculation
- [x] Profile versioning with SHA-256 hash

### Phase 3: Product Extraction ✅
- [x] Create base `ProductExtractor` class
- [x] Implement Uniqlo extractor (BeautifulSoup)
- [x] Factory pattern for extractor selection
- [x] URL pattern matching for site detection

### Phase 4: Cost Tracking ✅
- [x] Implement `CostTracker` service
- [x] Session cost breakdown endpoint (`/api/costs/session/{id}`)
- [x] Total cost endpoint (`/api/costs/total`)
- [x] Cached savings calculation

### Phase 5: API Integration ✅
- [x] Create `/api/analyze` endpoint
- [x] Integrate: extractors → AI provider → cost tracker → database
- [x] Create `/api/test-connection` endpoint
- [x] Add analysis caching logic (check DB before calling AI)

### Phase 6: Database Service Layer ✅
- [x] Product CRUD operations (`ProductService`)
- [x] Analysis CRUD operations (`AnalysisService`)
- [x] Profile CRUD operations (`ProfileService`)
- [x] Cache lookup logic (by product_url + profile_version)

### Phase 7: Testing Suite ✅
- [x] Database tests (schema, CRUD, cache lookup)
- [x] AI provider tests (mock Claude API, cost calculation)
- [x] API integration tests (full analysis flow)
- [x] Achieve >80% test coverage (currently 81%)

### Phase 8: Extension Foundation ✅
- [x] Firefox extension manifest (Manifest V3)
- [x] Content script injection with analysis overlay
- [x] Background service worker (API communication)
- [x] Extension popup UI
- [x] Settings storage (Firefox storage API)

### Phase 9: Style Quiz ✅
- [x] Quiz page UI with visual examples
- [x] Question flow implementation (7 questions)
- [x] Profile generation (structured JSON)
- [x] Storage in database with versioning

### Phase 10: Analysis Display ✅
- [x] Product page detection logic
- [x] Analysis box UI (collapsed/expanded states)
- [x] Full vs basic mode analysis
- [x] Outfit pairing suggestions display
- [x] Color-coded match score indicators
- [x] Basic mode quiz prompt

### Phase 11: Polish & Launch ✅
- [x] Comprehensive error handling in extension
- [x] Debug logging system (backend + extension)
- [x] Cost display in all locations
- [x] Performance optimization (fetch timeouts, static imports)
- [x] Image optimization utility (WebP conversion)

---

## Setup Required (Post-Merge)

See `POST_MERGE_SETUP.md` for:
- [ ] Configure Anthropic API key in `secrets.json`
- [ ] Install backend dependencies
- [ ] Build and load extension in Firefox
- [ ] Run test suite to verify setup

---

## Open Questions (Block V1)
1. Multi-site support - which sites after Uniqlo?
2. Quiz question refinement - need user testing
3. Beta launch strategy - invite-only vs public?

---

## Future Features (Post-MVP)
- [ ] Persistent all-time cost tracking
- [ ] Multi-device sync via passphrase
- [ ] Price history tracking
- [ ] Cloudflare Workers deployment option
- [ ] LM Studio local AI support
- [ ] Additional e-commerce sites (H&M, Zara, etc.)

---

*See `GroveAssistantSpec.md` for full product specification*

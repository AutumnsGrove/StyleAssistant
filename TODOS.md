# GroveAssistant - Development TODOs

## Current Focus: V1 MVP

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

### Phase 5: API Integration
- [ ] Create `/api/analyze` endpoint
- [ ] Integrate: extractors → AI provider → cost tracker → database
- [ ] Create `/api/test-connection` endpoint
- [ ] Add analysis caching logic (check DB before calling AI)

### Phase 6: Database Service Layer
- [ ] Product CRUD operations
- [ ] Analysis CRUD operations
- [ ] Profile CRUD operations
- [ ] Cache lookup logic (by product_url + profile_version)

### Phase 7: Testing Suite
- [ ] Database tests (schema, CRUD, cache lookup)
- [ ] AI provider tests (mock Claude API, cost calculation)
- [ ] API integration tests (full analysis flow)
- [ ] Achieve >80% test coverage

### Phase 8: Extension Foundation
- [ ] Firefox extension manifest (Manifest V3)
- [ ] Content script injection (DOM + fallback)
- [ ] Background service worker (API communication)
- [ ] Extension popup UI
- [ ] Settings storage (Firefox storage API)

### Phase 9: Style Quiz
- [ ] Quiz page UI with visual examples
- [ ] Question flow implementation (7 questions)
- [ ] Profile generation (structured JSON)
- [ ] Storage in database with versioning

### Phase 10: Analysis Display
- [ ] Product page detection logic
- [ ] Analysis box UI (collapsed/expanded states)
- [ ] Full vs basic mode analysis
- [ ] Outfit pairing suggestions display
- [ ] Color-coded match score indicators

### Phase 11: Polish & Launch
- [ ] Comprehensive error handling in extension
- [ ] Debug logging system
- [ ] Cost display in all locations
- [ ] Performance optimization
- [ ] Image optimization (WebP conversion)

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

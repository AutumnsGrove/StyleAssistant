-- GroveAssistant Database Schema
-- Enhanced schema with constraints and indexes for production use

-- User style profile
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY,
    profile_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product cache
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_url TEXT UNIQUE NOT NULL,
    site TEXT NOT NULL CHECK(site IN ('uniqlo')),
    title TEXT,
    price REAL CHECK(price >= 0),
    currency TEXT DEFAULT 'USD',
    description TEXT,
    materials TEXT,
    category TEXT,
    colors TEXT,
    sizes TEXT,
    image_data BLOB,
    raw_data TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis cache
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    profile_version TEXT NOT NULL,
    model_used TEXT NOT NULL CHECK(model_used IN (
        'claude-sonnet-4.5-20250929',
        'claude-haiku-4.5-20250929'
    )),
    analysis_type TEXT NOT NULL CHECK(analysis_type IN ('full', 'basic')),
    analysis_data TEXT NOT NULL,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    tokens_cache_read INTEGER DEFAULT 0,
    tokens_cache_write INTEGER DEFAULT 0,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost tracking log
CREATE TABLE IF NOT EXISTS cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    tokens_cache_read INTEGER DEFAULT 0,
    tokens_cache_write INTEGER DEFAULT 0,
    cost_usd REAL NOT NULL,
    request_type TEXT CHECK(request_type IN ('analysis', 'full', 'basic')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Debug log
CREATE TABLE IF NOT EXISTS debug_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK(level IN ('info', 'warning', 'error')),
    component TEXT,
    message TEXT NOT NULL,
    stack_trace TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_products_url ON products(product_url);
CREATE INDEX IF NOT EXISTS idx_analyses_lookup ON analyses(product_id, profile_version);
CREATE INDEX IF NOT EXISTS idx_cost_log_session ON cost_log(session_id, timestamp);

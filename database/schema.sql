CREATE TABLE IF NOT EXISTS heritage_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_cluster_id TEXT,
    title_original TEXT NOT NULL,
    title_zh TEXT,
    source_name TEXT NOT NULL,
    source_tier TEXT CHECK(source_tier IN ('core_official', 'wire_media', 'regional_media', 'specialist_media')),
    trust_level TEXT CHECK(trust_level IN ('high', 'medium')),
    language TEXT NOT NULL,
    country_region TEXT,
    pub_date DATETIME NOT NULL,
    url TEXT UNIQUE NOT NULL,
    summary_zh TEXT,
    raw_content JSON,
    translation_status TEXT DEFAULT 'pending',
    translation_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pub_date_tier ON heritage_news(pub_date DESC, source_tier ASC);
CREATE INDEX IF NOT EXISTS idx_event_cluster ON heritage_news(event_cluster_id);
CREATE INDEX IF NOT EXISTS idx_language ON heritage_news(language);
CREATE INDEX IF NOT EXISTS idx_source_tier ON heritage_news(source_tier);

CREATE TABLE IF NOT EXISTS source_health (
    source_name TEXT PRIMARY KEY,
    last_successful_fetch DATETIME,
    failure_count_24h INTEGER DEFAULT 0,
    total_articles INTEGER DEFAULT 0,
    avg_articles_per_week REAL,
    status TEXT CHECK(status IN ('active', 'dormant', 'unstable', 'rejected')),
    last_check DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_data (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(255),
    author TEXT,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT NOT NULL UNIQUE,
    image_url TEXT,
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB NOT NULL,
    commodity VARCHAR(64) NOT NULL DEFAULT 'lithium',
    region VARCHAR(128),
    country VARCHAR(128),
    project_name TEXT,
    event_type VARCHAR(128),
    sentiment_score NUMERIC(6, 3)
);

CREATE INDEX IF NOT EXISTS idx_event_data_published_at ON event_data (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_data_project_name ON event_data (project_name);
CREATE INDEX IF NOT EXISTS idx_event_data_event_type ON event_data (event_type);

CREATE TABLE IF NOT EXISTS mining_projects (
    id BIGSERIAL PRIMARY KEY,
    project_name TEXT NOT NULL,
    country VARCHAR(128) NOT NULL,
    region VARCHAR(128),
    owner_company TEXT,
    resource_type VARCHAR(64),
    status VARCHAR(64),
    estimated_resource_mt_lce NUMERIC(14, 3),
    annual_capacity_t_lce NUMERIC(14, 3),
    expected_start_year INTEGER,
    last_news_at TIMESTAMPTZ,
    risk_signal_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_name, country)
);

CREATE INDEX IF NOT EXISTS idx_mining_projects_country ON mining_projects (country);
CREATE INDEX IF NOT EXISTS idx_mining_projects_status ON mining_projects (status);

CREATE TABLE IF NOT EXISTS cost_curve (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES mining_projects(id) ON DELETE CASCADE,
    as_of_date DATE NOT NULL,
    cash_cost_usd_t_lce NUMERIC(14, 2),
    sustaining_cost_usd_t_lce NUMERIC(14, 2),
    all_in_cost_usd_t_lce NUMERIC(14, 2),
    production_t_lce NUMERIC(14, 2),
    cost_percentile NUMERIC(6, 3),
    source TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, as_of_date)
);

CREATE INDEX IF NOT EXISTS idx_cost_curve_as_of_date ON cost_curve (as_of_date DESC);

CREATE TABLE IF NOT EXISTS risk_scores (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES mining_projects(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    operational_risk NUMERIC(6, 3) NOT NULL,
    jurisdiction_risk NUMERIC(6, 3) NOT NULL,
    market_risk NUMERIC(6, 3) NOT NULL,
    news_risk NUMERIC(6, 3) NOT NULL,
    total_risk NUMERIC(6, 3) NOT NULL,
    rationale JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, score_date)
);

CREATE TABLE IF NOT EXISTS etl_run_log (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    records_processed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);


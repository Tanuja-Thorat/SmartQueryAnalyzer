-- =============================================================================
-- QueryWise "APP" Database Schema
-- =============================================================================
-- This is QueryWise's OWN storage: query history, analysis results, and
-- index recommendations. It is separate from the TARGET database you are
-- analyzing (schema.sql / seed.sql), even if both happen to live in the
-- same PostgreSQL database for local development.
--
-- NOTE: The FastAPI backend automatically creates these tables on startup
-- via SQLAlchemy (Base.metadata.create_all) if they don't already exist, so
-- running this file by hand is OPTIONAL for a fresh install. It's provided
-- so you can inspect the exact structure, or set it up manually / ahead of
-- time (e.g. in a CI pipeline). Safe to re-run: tables are dropped first.
-- =============================================================================

DROP TABLE IF EXISTS index_recommendations CASCADE;
DROP TABLE IF EXISTS query_analysis CASCADE;
DROP TABLE IF EXISTS queries CASCADE;

-- -----------------------------------------------------------------------------
-- queries — one row per unique SQL query text (de-duplicated by hash)
-- -----------------------------------------------------------------------------
CREATE TABLE queries (
    id          SERIAL PRIMARY KEY,
    query_text  TEXT NOT NULL,
    query_hash  VARCHAR(64) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_queries_query_hash ON queries(query_hash);

-- -----------------------------------------------------------------------------
-- query_analysis — one row per EXPLAIN run against a query
-- -----------------------------------------------------------------------------
CREATE TABLE query_analysis (
    id              SERIAL PRIMARY KEY,
    query_id        INTEGER NOT NULL REFERENCES queries(id),

    total_cost      DOUBLE PRECISION DEFAULT 0,
    startup_cost    DOUBLE PRECISION DEFAULT 0,
    estimated_rows  INTEGER DEFAULT 0,
    actual_rows     INTEGER,
    execution_time  DOUBLE PRECISION,      -- milliseconds

    health_score    INTEGER DEFAULT 0,
    health_status   VARCHAR(32) DEFAULT 'Unknown',

    scan_type       VARCHAR(64),           -- e.g. "Seq Scan", "Index Scan"
    is_slow         INTEGER DEFAULT 0,     -- 0/1 boolean flag
    primary_table   VARCHAR(128),          -- main FROM table (dashboard stats)

    issues          JSON DEFAULT '[]',      -- list[str]
    plan_tree       JSON DEFAULT '{}',      -- simplified plan tree for the UI
    raw_plan        JSON DEFAULT '{}',      -- raw EXPLAIN JSON (debug)

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_query_analysis_primary_table ON query_analysis(primary_table);

-- -----------------------------------------------------------------------------
-- index_recommendations — one row per suggested index derived from an analysis
-- -----------------------------------------------------------------------------
CREATE TABLE index_recommendations (
    id                      SERIAL PRIMARY KEY,
    query_analysis_id       INTEGER NOT NULL REFERENCES query_analysis(id),

    table_name              VARCHAR(128) NOT NULL,
    columns                 JSON DEFAULT '[]',   -- list[str]
    recommended_index_sql   TEXT NOT NULL,
    reason                  TEXT,
    estimated_improvement   DOUBLE PRECISION DEFAULT 0,  -- percentage

    status                  VARCHAR(32) DEFAULT 'suggested',  -- suggested / dismissed
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

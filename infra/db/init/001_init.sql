-- 001_init.sql — initial schema for the Personalized Learning Bot.
-- Auto-run by Postgres on first container start (mounted into
-- /docker-entrypoint-initdb.d via docker-compose). Also usable as a manual
-- migration: `psql "$DATABASE_URL" -f infra/db/init/001_init.sql`.

-- Extensions -------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector, for retrieval_cache

-- Enums ------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mastery_level') THEN
        CREATE TYPE mastery_level AS ENUM ('unseen', 'learning', 'mastered');
    END IF;
END$$;

-- Core learner tables ----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS topics (
    id          SERIAL PRIMARY KEY,
    slug        TEXT        NOT NULL UNIQUE,
    title       TEXT        NOT NULL,
    description TEXT
);

-- A topic's syllabus graph. `prerequisites` holds concept ids that should be
-- learned/mastered before this concept is taught (adaptive ordering).
CREATE TABLE IF NOT EXISTS concepts (
    id           SERIAL PRIMARY KEY,
    topic_id     INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    slug         TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    summary      TEXT,
    prerequisites INTEGER[] NOT NULL DEFAULT '{}',
    order_hint   INTEGER NOT NULL DEFAULT 0,
    UNIQUE (topic_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_concepts_topic ON concepts(topic_id);

-- Per-user mastery of each concept.
CREATE TABLE IF NOT EXISTS learner_concept_state (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id   INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery      mastery_level NOT NULL DEFAULT 'unseen',
    attempts     INTEGER NOT NULL DEFAULT 0,
    correct      INTEGER NOT NULL DEFAULT 0,
    last_seen_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, concept_id)
);

-- Conversation history ---------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id   INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS messages (
    id         SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role       TEXT    NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content    TEXT    NOT NULL,
    citations  JSONB   NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

-- MCP registry (the scalability seam) ------------------------------------
-- New MCP servers are added as rows here; the topic router reads this table
-- to decide which server(s) to call. No agent-loop code changes required.
CREATE TABLE IF NOT EXISTS mcp_registry (
    id          SERIAL PRIMARY KEY,
    name        TEXT    NOT NULL UNIQUE,
    endpoint    TEXT    NOT NULL,
    auth_ref    TEXT,                       -- name of an env var holding the secret
    topics      TEXT[]  NOT NULL DEFAULT '{}',
    tool_schema JSONB,                      -- discovered on registration
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    priority    INTEGER NOT NULL DEFAULT 100,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Retrieval cache (pgvector) --------------------------------------------
-- MCP results are embedded and cached to cut latency + repeat calls.
-- NOTE: embedding dimension must match your embedding model. 1536 =
-- OpenAI text-embedding-3-small. Change the number if you switch models.
CREATE TABLE IF NOT EXISTS retrieval_cache (
    id         SERIAL PRIMARY KEY,
    topic      TEXT NOT NULL,
    query_norm TEXT NOT NULL,
    embedding  VECTOR(1536),
    payload    JSONB NOT NULL,
    source_mcp TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_retrieval_topic_query
    ON retrieval_cache(topic, query_norm);
-- Approximate-nearest-neighbour index for semantic lookups.
CREATE INDEX IF NOT EXISTS idx_retrieval_embedding
    ON retrieval_cache USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

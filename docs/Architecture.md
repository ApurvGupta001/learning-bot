# Architecture — Personalized Learning Bot

## 1. System overview

```
        Browser
   ┌─────────────────────────┐
   │  Next.js (App Router)    │  chat UI + (future) dashboard
   └───────────┬─────────────┘
               │  HTTP POST + SSE stream
   ┌───────────▼─────────────┐
   │  FastAPI backend        │
   │                         │
   │   Agent Loop (custom)   │  pick concept → retrieve → teach (stream)
   │        │        │       │
   │        │        ▼       │
   │        │   MCP Client   │──► MCP Registry (DB table) ──► [ CUDA MCP ] (+more)
   │        ▼                │
   │   LLM wrapper (Claude / stub)
   └───────────┬─────────────┘
               │  SQLAlchemy
   ┌───────────▼─────────────┐
   │  PostgreSQL + pgvector  │  users, concepts, mastery, messages,
   └─────────────────────────┘  mcp_registry, retrieval_cache (vectors)
```

## 2. Request flow (one chat message)

1. Browser `POST /sessions/{id}/message` with `{ "content": "..." }`.
2. Backend runs `run_turn()`: pick concept → `retriever.retrieve(topic, q)` →
   build prompt (instructions + docs + user message) → `llm.stream(...)`.
3. Tokens stream out as SSE frames: `data: <json-encoded token>\n\n`, ending with
   `data: [DONE]\n\n`.
4. Frontend reads the stream via `fetch` + `ReadableStream`, decodes each token,
   and appends it to the assistant bubble.

## 3. Technical stack

| Concern | Choice |
|---|---|
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| Orchestration | Custom async agent loop (no LLM framework) |
| LLM | Anthropic Claude via official SDK (streaming) + stub fallback |
| Retrieval | MCP (Model Context Protocol) via `Retriever` interface |
| Data | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy 2.0 (typed models) |
| Config | pydantic-settings (env / `.env`) |
| Packaging | Docker + Docker Compose |

## 4. Folder & file structure

```
learning-bot/
├── README.md
├── Makefile                     # up/down/logs, backend/frontend/db helpers
├── .gitignore
│
├── backend/                     # FastAPI service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py              # app + /health + router registration
│       ├── config.py            # settings (env-driven)
│       ├── schemas.py           # Pydantic request/response models
│       ├── db/
│       │   ├── base.py          # engine, SessionLocal, get_db()
│       │   └── models.py        # SQLAlchemy ORM models
│       ├── agent/
│       │   ├── llm.py           # Claude streaming + stub fallback
│       │   └── loop.py          # run_turn(): the agent loop
│       ├── mcp/
│       │   ├── client.py        # Retriever interface + Stub/Cuda + factory
│       │   └── registry.py      # servers_for_topic() topic router
│       └── routers/
│           └── sessions.py      # POST /sessions/{id}/message (SSE)
│
├── frontend/                    # Next.js web app
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.mjs
│   ├── .env.local.example
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # topic picker (home)
│   │   ├── chat/page.tsx        # streaming chat UI
│   │   └── globals.css
│   └── lib/
│       └── api.ts               # API client + SSE stream reader
│
├── infra/                       # deployment
│   ├── docker-compose.yml       # db + backend + frontend
│   ├── .env.example             # compose secrets (ANTHROPIC_API_KEY, ...)
│   └── db/
│       ├── README.md
│       └── init/001_init.sql    # schema (auto-run on first DB start)
│
└── docs/                        # PRD, Architecture, Rules, Phases, Design,
                                 # Memory, design-spec, interview prep
```

## 5. Data model (summary)

- `users` — learners.
- `topics` — subjects (e.g., cuda).
- `concepts` — syllabus nodes; `prerequisites` (int[]) enables adaptive ordering.
- `learner_concept_state` — per-user mastery (`unseen|learning|mastered`),
  attempts, correct.
- `sessions`, `messages` — chat history (`messages.citations` is JSONB).
- `mcp_registry` — registered MCP servers; `topics[]`, `enabled`, `priority`.
- `retrieval_cache` — `embedding vector(1536)` + payload; `ivfflat` ANN index.

SQL (`infra/db/init/001_init.sql`) is the schema source of truth; ORM models
mirror it.

## 6. Key architectural principles

- **Interface-first retrieval:** the agent depends on a `Retriever` abstraction,
  so MCP servers are swappable and testable (stub today, CUDA next).
- **Data-driven scalability:** the `mcp_registry` table (not code) decides which
  doc-sources serve a topic.
- **Graceful degradation:** stub LLM + stub retriever mean the app always runs.
- **Stateless backend:** all state in Postgres → horizontal scaling later.
- **Streaming everywhere:** SSE with JSON-framed tokens (newline-safe).

## 7. Environments & ports

| Service | Port (host) | Notes |
|---|---|---|
| Frontend | 3000 | Next.js |
| Backend | 8000 | FastAPI; `/health` |
| Postgres | 5433 → 5432 | host 5433 avoids clashing with a local Postgres |

## 8. Deployment

- Local dev: run services directly (venv + npm) or `docker compose up`.
- The Postgres init-hook applies the schema on first boot.
- Frontend `NEXT_PUBLIC_API_BASE_URL` is a **build-time** arg (inlined into the
  browser bundle).

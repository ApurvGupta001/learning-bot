# Personalized Learning Bot

An MCP-powered adaptive learning chatbot. Pick a topic (starting with CUDA) and the bot
teaches it step-by-step — grounding every explanation in real documentation fetched live
through Model Context Protocol (MCP) servers, generating exercises, grading answers, and
tracking mastery so it can adapt what it teaches next.

> Full design: see [`docs/design-spec.md`](docs/design-spec.md).

## Why this exists

Most demo chatbots are one-shot RAG. This one layers three harder things:

1. **A custom agent loop** (no framework) — retrieval, grading, and state transitions are all explicit.
2. **MCP tool orchestration** behind a pluggable registry — new doc sources are a config change.
3. **Stateful learner modeling** — a concept graph + mastery tracking drive adaptive teaching.

## Stack

- **Frontend:** Next.js / TypeScript (SSE streaming)
- **Backend:** FastAPI / Python — custom agent loop over an LLM SDK
- **MCP:** official Python MCP SDK (client); NVIDIA CUDA MCP server first
- **Data:** Postgres + pgvector
- **Infra:** Docker Compose (local dev)

## Repository layout

```
learning-bot/
├── backend/      FastAPI app, agent loop, MCP client layer
├── frontend/     Next.js chat UI + progress dashboard
├── infra/        docker-compose, DB init/migrations
└── docs/         design spec
```

## Status

Early scaffold — built incrementally. See the checklist below.

- [x] Repo structure
- [x] Backend skeleton (FastAPI)
- [x] Database schema + migrations
- [x] Frontend skeleton (Next.js)
- [x] Agent loop + MCP client skeleton
- [x] Docker Compose + dependency install

## Getting started

### Option A — Docker Compose (whole stack)

Requires Docker. Brings up Postgres+pgvector (schema auto-applied), the API, and the web app.

```bash
cd infra
cp .env.example .env      # optional: add ANTHROPIC_API_KEY; blank = stub tutor
docker compose up --build
```

Then open http://localhost:3000 (API at http://localhost:8000, `/health` to check).
From the repo root you can also just run `make up`.

### Option B — Run services directly

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend (in another terminal):

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

With Option B you provide your own Postgres and apply `infra/db/init/001_init.sql`
(`make db-migrate`). Leave `ANTHROPIC_API_KEY` blank to use the stub tutor.

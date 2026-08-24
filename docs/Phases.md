# Phases — Build plan & progress

The project is built in small, self-contained phases. ✅ done · 🔜 next · ⬜ later.

## Phase 0 — Foundations ✅
Repo structure, README, `.gitignore`, docs.
**Done:** folder layout, git, design spec.

## Phase 1 — Backend skeleton ✅
FastAPI app + `/health` + env-driven config.
**Done:** `app/main.py`, `app/config.py`, `requirements.txt`.

## Phase 2 — Database ✅
Postgres + pgvector schema + ORM models.
**Done:** `infra/db/init/001_init.sql` (8 tables, enum, `ivfflat` index),
`app/db/base.py`, `app/db/models.py`.

## Phase 3 — Frontend skeleton ✅
Next.js App Router: topic picker + streaming chat + API client.
**Done:** `app/page.tsx`, `app/chat/page.tsx`, `lib/api.ts`, `globals.css`.

## Phase 4 — Agent loop + MCP client ✅
Custom agent loop, LLM wrapper (Claude + stub), `Retriever` interface, streaming
chat endpoint.
**Done:** `app/agent/llm.py`, `app/agent/loop.py`, `app/mcp/client.py`,
`app/mcp/registry.py`, `app/routers/sessions.py`. Chat streams end-to-end.

## Phase 5 — Containerization ✅
Docker Compose (db + backend + frontend), Dockerfiles.
**Done:** `infra/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.
One command runs the whole stack.

---

## Phase 6 — Real CUDA MCP retrieval ✅
Wired `CudaMCPRetriever`: connects to the CUDA MCP server via the MCP SDK
(streamable-HTTP or SSE), **auto-discovers** the search tool, calls it, and maps
results to `RetrievedDoc` via `_coerce_docs` (structured or text-block shapes).
Config: `CUDA_MCP_URL`, `CUDA_MCP_TOOL`, `CUDA_MCP_API_KEY`, `CUDA_MCP_TRANSPORT`,
`MCP_QUERY_ARG`. Agent loop appends a deterministic **Sources** footer when docs
are retrieved. Graceful: failures degrade to "no docs". Parser covered by
`backend/tests/test_mcp_client.py` (6 tests, all pass).
**Done — to activate:** set `CUDA_MCP_URL` (+ key if required) in your env.
**Remaining to fully close in prod:** confirm live against the real endpoint and
seed an `mcp_registry` row (registry-driven routing is Phase 10).

## Phase 7 — Concept graph seed ⬜
Seed CUDA `topics` + `concepts` (with prerequisites) and an initial ordering.
**Acceptance:** the syllabus exists in the DB and drives lesson order.

## Phase 8 — Teach / quiz / grade + mastery ⬜
Generate exercises, grade answers (rubric prompt), update
`learner_concept_state`; implement `pick_next_concept()` from mastery +
prerequisites. Persist `sessions`/`messages`.
**Acceptance:** mastery changes with performance; next concept adapts.

## Phase 9 — Progress dashboard ⬜
Frontend view of the concept graph + per-concept mastery.
**Acceptance:** learner can see progress at a glance.

## Phase 10 — Retrieval cache + MCP registry admin ⬜
Populate/query `retrieval_cache` (pgvector) to cut latency/cost; add routes to
list/enable/prioritize MCP servers; prove pluggability with a second (stub) MCP.
**Acceptance:** cache hits skip network calls; a new source is added via config.

## Phase 11 — Polish & deploy ⬜
Auth (minimal), tests/golden-set eval, README demo script, hosted deploy
(Vercel + Railway/Fly).
**Acceptance:** live URL; green CI; smooth demo.

---

### Sequencing notes
- Phases 6–8 are the "make it actually teach" core; do them in order.
- Each phase must keep the app runnable (stub fallbacks) and update `Memory.md`.

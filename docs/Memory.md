# Memory — Project progress & context

> Living context file. Read this first when starting a new AI session so you
> don't re-read the whole codebase. Update it after every meaningful change.
> Last updated: 2026-08-23.

## 1. What this project is
Personalized Learning Bot — an adaptive tutor that teaches a topic (CUDA first)
step by step, grounds answers in real docs via MCP, and tracks mastery. See
`PRD.md`, `Architecture.md`, `Phases.md`, `Rules.md`, `Design.md`.

## 2. Current status: MVP scaffold COMPLETE
Chat works end-to-end (browser → FastAPI → agent loop → LLM → streamed reply).
Runs with a **stub** when no API key is set, and with **real Claude** when
`ANTHROPIC_API_KEY` is provided.

Phases done: 0 Foundations, 1 Backend skeleton, 2 Database, 3 Frontend, 4 Agent
loop + MCP client, 5 Docker Compose. (See `Phases.md`.)

## 3. What works right now
- `GET /health` returns ok.
- `POST /sessions/{id}/message` streams a tutor reply as SSE (JSON-framed tokens,
  ends with `[DONE]`).
- Frontend chat page streams tokens live; topic picker links to `/chat?topic=cuda`.
- Postgres + pgvector schema auto-applies on first DB start.
- `docker compose up` runs db + backend + frontend together.

## 4. What's NOT built yet (next work)
- **Phase 6 DONE + WIRED:** `CudaMCPRetriever` implemented — connects via MCP SDK,
  auto-discovers the search tool AND its query-arg (`_pick_query_arg` reads the
  tool inputSchema), maps results (`_coerce_docs`), appends a Sources footer.
  `CUDA_MCP_URL=https://api.copilot.nsight.ngc.nvidia.com/mcp/cuda-docs` is now
  set in backend/.env and infra/.env (transport http). Add `CUDA_MCP_API_KEY`
  (NGC token) only if the server returns 401. Not yet confirmed live from here
  (sandbox can't reach the endpoint). Tests: `backend/tests/test_mcp_client.py`
  (10 pass).
- **Phase 7 (next):** concept-graph seed data (tables exist, empty).
- Teach/quiz/grade cycle + mastery updates + `pick_next_concept()` (currently a
  stub returning "Introduction").
- Message/session persistence (endpoint doesn't write to DB yet).
- Progress dashboard; retrieval cache population; MCP registry admin routes.

## 5. Key decisions (and why)
- Custom agent loop, **no LangChain** — explicit, explainable.
- **pgvector**, not a separate vector DB — one datastore.
- **SSE over fetch** (not EventSource) — must POST the message body.
- **MCP registry table** drives doc-sources — add sources via config, not code.
- **Stub fallbacks** for LLM + retriever — app always runs.
- SQL migration is schema source of truth; ORM models mirror it.

## 6. Gotchas / hard-won facts
- **FastAPI must be `>=0.115.3`** (starlette `>=0.39`) to coexist with `mcp`.
  Pinned `fastapi>=0.115.6,<0.116`.
- **Next.js pinned to `14.2.35`** (security patch). Do NOT `npm audit fix --force`
  (jumps to Next 15).
- **LLM model is config** (`ANTHROPIC_MODEL`, default `claude-sonnet-5`).
  `-latest` aliases 404 on the current API. Valid IDs (Aug 2026):
  `claude-sonnet-5`, `claude-opus-5`, `claude-haiku-4-5-20251001`, `claude-fable-5`.
- **Docker DB host port is 5433** (`5433:5432`) to avoid clashing with a local
  Postgres. Backend reaches DB internally at `db:5432`.
- **The Docker backend reads `infra/.env`**, not `backend/.env`. No key there →
  stub tutor.
- `docker compose up` runs in foreground (looks "stuck"); use `-d` for detached.
- `NEXT_PUBLIC_API_BASE_URL` is inlined at **build time** (Dockerfile build arg).

## 7. How to run (quick)
```bash
# whole stack
cd infra && cp .env.example .env   # add ANTHROPIC_API_KEY (blank = stub)
docker compose up -d --build       # http://localhost:3000
```

## 8. File map (where things live)
- Agent loop: `backend/app/agent/loop.py` (`run_turn`)
- LLM wrapper: `backend/app/agent/llm.py` (Claude stream + stub)
- Retrieval: `backend/app/mcp/client.py` (interface + Stub/Cuda + factory),
  `backend/app/mcp/registry.py` (topic router)
- Chat endpoint: `backend/app/routers/sessions.py`
- Schema: `infra/db/init/001_init.sql`; ORM: `backend/app/db/models.py`
- Frontend chat + client: `frontend/app/chat/page.tsx`, `frontend/lib/api.ts`

## 9. Immediate next action
Start **Phase 7**: seed CUDA `topics` + `concepts` (with prerequisites) so the
syllabus drives lesson order. (Phase 6 retrieval is implemented; to see it live,
set `CUDA_MCP_URL` and ask a CUDA question — a Sources footer should appear.)

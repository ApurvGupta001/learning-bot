# Rules — Guardrails for AI-assisted development

Rules the AI (and humans) should follow when building this project. Keep changes
consistent, safe, and explainable.

## 1. Golden rules
- **Small, reviewable steps.** One coherent change at a time; explain *why* and
  the *alternatives* considered after each step.
- **Don't break a running app.** The project must always start (stubs guarantee
  this). If a change needs a key/DB/MCP, keep a graceful fallback.
- **Keep SQL and ORM models in sync.** `infra/db/init/001_init.sql` is the schema
  source of truth; update `backend/app/db/models.py` to match.
- **No secrets in code or Git.** Secrets live only in `.env` files (gitignored).
  Add new config to the relevant `.env.example`.

## 2. Tech choices — use / avoid
**Use**
- Backend: FastAPI, SQLAlchemy 2.0, pydantic-settings, the official `mcp` and
  `anthropic` SDKs, psycopg 3.
- Frontend: Next.js App Router + TypeScript. Plain CSS in `globals.css` for now.
- Data: PostgreSQL + pgvector only (no second datastore).

**Avoid (without discussion)**
- LLM frameworks (LangChain/LlamaIndex) — the agent loop stays custom & explicit.
- A separate vector database — use pgvector.
- Heavy frontend UI kits this early — keep the skeleton lean.
- Browser storage APIs in demo artifacts (`localStorage`/`sessionStorage`).
- New runtime dependencies unless justified; prefer the standard library.

## 3. Versioning & dependencies
- Pin compatible ranges, not fragile exacts. Known constraint: **FastAPI must be
  `>=0.115.3`** (needs `starlette>=0.39`) to coexist with `mcp`.
- **Next.js must stay on a patched release** (currently `14.2.35`). Patch within
  the major line; do **not** run `npm audit fix --force` (it can jump to Next 15).
- Never hardcode external identifiers that can change (e.g., LLM model names).
  Use config: `ANTHROPIC_MODEL` (valid IDs incl. `claude-sonnet-5`,
  `claude-opus-5`, `claude-haiku-4-5-20251001`). `-latest` aliases may 404.

## 4. Error handling
- **Streaming must never crash the request.** Wrap generation in
  try/except/finally and always emit a final `data: [DONE]`.
- Surface external errors as **readable messages** (LLM/MCP failures show what
  went wrong, e.g., the bad model ID), not stack traces to the user.
- Validate inputs with Pydantic (`content` min length ≥ 1).
- Prefer graceful degradation (stub) over hard failure where sensible.

## 5. Security & privacy
- Grounded answers should **cite sources**; don't present model guesses as
  sourced facts. The tutor must disclose when it lacks docs.
- CORS is limited to the frontend origin in dev; tighten for production.
- Don't log secrets. Don't echo internal prompts/scaffolding to users.

## 6. Code style & structure
- Keep the **agent loop explicit**: pick concept → retrieve → build prompt →
  stream. No hidden control flow.
- New API routes go under `backend/app/routers/` and are registered in `main.py`.
- New doc-sources are added as **`mcp_registry` rows/config**, not new code paths
  in the agent loop.
- Type everything reasonably (Python type hints, TS types).

## 7. Testing & verification
- Syntax/type-check before claiming done.
- For tricky protocols (e.g., SSE framing), add a round-trip test.
- Unit-test pure logic (concept selection, mastery transitions) without needing a
  live DB/LLM.
- Keep a golden-set eval for retrieval grounding once MCP is wired.

## 8. Definition of done (per change)
- App still starts (stub path works).
- SQL ↔ ORM in sync; `.env.example` updated if config added.
- Explanation of why + alternatives provided.
- `Memory.md` updated with the new state.

# Personalized Learning Bot — Project Guide & Interview Prep

A complete, beginner-friendly walkthrough of everything built so far, the ideas
behind it, the bugs we hit and fixed, and a large bank of interview questions
**with model answers**. Read it top to bottom the first time; use it as a
reference after that.

---

## Part 1 — What is this project, in plain English?

Imagine a private tutor that teaches you a topic (we started with **CUDA**, the
programming model for NVIDIA GPUs). Instead of making things up, the tutor looks
up **real documentation** before answering, teaches one concept at a time, gives
you exercises, checks your answers, and remembers what you've learned so it knows
what to teach next.

Three things make it more than a toy chatbot:

1. **It's grounded in real docs.** It fetches official documentation live through
   a standard called **MCP** (Model Context Protocol) and teaches from that,
   instead of relying only on what the AI model already "remembers." This reduces
   made-up answers (hallucinations).
2. **It has memory of your progress.** It tracks which concepts you've mastered
   using a database, so lessons adapt to you.
3. **It's built to grow.** New documentation sources (GitHub, other subjects) can
   be added as configuration — no rewriting the core logic.

> Why this is a strong portfolio project: most demos are "ask a question, get an
> answer." This one shows **retrieval + orchestration + state + deployment** —
> the pieces real AI products are actually made of.

---

## Part 2 — The big picture (architecture)

Think of the system as four cooperating parts:

```
   [ Browser: Next.js web app ]          <- what the user sees (chat UI)
              |  (HTTP + streaming)
   [ Backend: FastAPI (Python) ]         <- the brain: receives messages,
              |                              runs the "agent loop"
       -------+-------------
       |                   |
  [ MCP servers ]     [ PostgreSQL + pgvector ]
  (real docs)         (users, progress, cached docs)
```

- **Frontend (Next.js):** the chat page in the browser. Sends your message to the
  backend and displays the reply as it streams in, word by word.
- **Backend (FastAPI):** the core. It runs the **agent loop** — a step-by-step
  routine that decides what to teach, fetches supporting docs, and streams the
  answer back.
- **MCP layer:** the doorway to external documentation. Today it's a placeholder
  (a "stub"); next we connect the real NVIDIA CUDA docs.
- **Database (Postgres + pgvector):** stores users, topics, the concept syllabus,
  each learner's mastery, chat history, the registry of MCP servers, and a cache
  of retrieved docs.

### A single message's journey (very important to understand)

1. You type "Teach me threads" and hit send in the browser.
2. The frontend sends an HTTP `POST` to the backend endpoint
   `/sessions/demo/message`.
3. The backend's **agent loop** runs: pick a concept → ask the MCP layer for
   relevant docs → build a prompt (instructions + docs + your question) → ask the
   LLM to generate the lesson.
4. The LLM's answer streams back **token by token** (a token ≈ a word-piece).
5. Each token is sent to the browser as a small **Server-Sent Event (SSE)**.
6. The frontend appends each token to the chat bubble, so you watch the answer
   appear live.

---

## Part 3 — The technology stack, explained for beginners

| Layer | Tool | What it is | Why we chose it |
|---|---|---|---|
| Frontend | **Next.js** (React + TypeScript) | Framework for building web apps | Industry standard; file-based routing; easy streaming + deploy |
| Backend | **FastAPI** (Python) | Framework for building web APIs | Fast, async-native (great for streaming), auto docs, huge AI ecosystem |
| Config | **pydantic-settings** | Loads settings from environment variables with type-checking | Keeps secrets out of code; validates values |
| Database | **PostgreSQL** | A relational (SQL) database | Reliable, powerful, great for related data |
| Vector search | **pgvector** | A Postgres extension that stores AI "embeddings" | Lets us do semantic search **inside** Postgres — no separate database |
| ORM | **SQLAlchemy** | Lets Python code talk to the database with objects | Type-safe queries; avoids hand-writing SQL everywhere |
| AI model | **Anthropic Claude** | The large language model (LLM) | Generates the tutoring text |
| Docs access | **MCP** (Model Context Protocol) | A standard way for AIs to call external tools/data | Plug in new doc sources without custom glue code |
| Packaging | **Docker + Docker Compose** | Runs each part in an isolated "container" | One command spins up the whole system anywhere |

### Key concepts in one paragraph each

- **API (Application Programming Interface):** a set of URLs the frontend calls to
  make the backend do things (e.g., `POST /sessions/demo/message`).
- **LLM (Large Language Model):** the AI (Claude) that produces human-like text.
  It doesn't "know" your private data unless you give it in the prompt.
- **RAG (Retrieval-Augmented Generation):** the pattern of *retrieving* real
  documents and feeding them to the LLM so its answer is grounded in facts. Our
  MCP retrieval is a form of RAG.
- **MCP (Model Context Protocol):** a standard "plug" that lets an AI app call
  external tools/data sources (like a documentation search) in a uniform way.
- **Embedding:** a list of numbers that represents the *meaning* of a piece of
  text. Similar meanings → similar numbers. pgvector stores these so we can find
  "documents most similar to this question."
- **Streaming (SSE):** instead of waiting for the whole answer, the server sends
  it in small pieces as it's generated, so the UI feels alive.
- **Container (Docker):** a lightweight, self-contained box holding an app plus
  everything it needs to run, so it behaves the same on any machine.

---

## Part 4 — What we built, step by step

The project was built in six deliberate steps, each runnable on its own.

### Step 1 — Repository structure
Created the folder layout (`backend/`, `frontend/`, `infra/`, `docs/`), a README,
and a `.gitignore` (so secrets and huge folders never get committed).
**Beginner note:** `.gitignore` is a list of files Git should ignore — like
`.env` (secrets) and `node_modules/` (downloaded libraries).

### Step 2 — Backend skeleton (FastAPI)
A minimal running API with a `/health` endpoint that returns `{"status":"ok"}`,
plus configuration loaded from environment variables.
**Why a health check first?** It gives you something deployable and testable
before any real logic — you can confirm "the server is alive."

### Step 3 — Database schema (Postgres + pgvector)
Wrote the SQL that creates all tables: `users`, `topics`, `concepts` (the
syllabus, where each concept lists its prerequisites), `learner_concept_state`
(who has mastered what), `sessions` and `messages` (chat history), `mcp_registry`
(the list of doc sources), and `retrieval_cache` (stored embeddings of fetched
docs). Also created matching SQLAlchemy models so Python can query them.
**Beginner note:** a "schema" is the blueprint of your tables and their columns.

### Step 4 — Frontend skeleton (Next.js)
A home page listing topics and a chat page that streams replies. `lib/api.ts`
contains the code that talks to the backend and reads the streamed response.

### Step 5 — Agent loop + MCP client (the core)
- An **LLM wrapper** that streams from Claude when an API key is set, or a
  harmless **stub** (canned response) when it isn't — so the app always runs.
- A **Retriever interface** with a `StubRetriever` (returns nothing yet) and a
  `CudaMCPRetriever` placeholder for the real NVIDIA CUDA docs.
- The **agent loop** (`run_turn`): pick concept → retrieve docs → build prompt →
  stream the lesson.
- The **streaming endpoint** `POST /sessions/{id}/message` that sends the lesson
  back as SSE.

### Step 6 — Docker Compose (run everything with one command)
`docker-compose.yml` starts three containers: Postgres+pgvector (which auto-runs
our schema on first boot), the backend, and the frontend. Dockerfiles describe
how to build the backend and frontend images.
**Result:** `docker compose up` brings up the entire system.

---

## Part 5 — Design decisions & trade-offs (the "why")

Interviewers love "why did you choose X over Y." Here are the big ones.

- **Custom agent loop instead of a framework (e.g., LangChain).**
  *Why:* full control and the ability to explain every step; fewer heavy
  dependencies. *Trade-off:* we write more ourselves, but nothing is hidden.

- **pgvector instead of a separate vector database (Pinecone/Chroma).**
  *Why:* one database to run and reason about; plenty fast at our scale.
  *Trade-off:* a dedicated vector DB scales further, but adds cost and a network
  hop we don't need yet.

- **SSE streaming over `fetch` instead of WebSockets.**
  *Why:* we only need one-way streaming (server → browser); SSE is simpler and
  works over plain HTTP. *Trade-off:* no bidirectional channel, which we don't
  need. We used `fetch` + a stream reader (not the browser's `EventSource`)
  because we must **POST** the message, and `EventSource` only supports GET.

- **A data-driven MCP registry (a database table) instead of hardcoding servers.**
  *Why:* adding a new documentation source becomes "insert a row," not "change
  code." This is the scalability story.

- **Graceful stub fallbacks (LLM and retriever).**
  *Why:* the app always runs — no API key, no live MCP, no problem. Great for
  demos and tests.

- **SQL migration file as the source of truth (not auto-created from code).**
  *Why:* precise control over extensions (pgvector), enums, and special indexes
  (the `ivfflat` vector index). *Trade-off:* we keep SQL and models in sync by
  hand; a tool like Alembic can automate this later.

---

## Part 6 — Real problems we hit and how we fixed them
*(These make excellent "tell me about a bug" interview stories.)*

1. **Dependency conflict: FastAPI vs MCP.**
   Installing failed because `fastapi 0.115.0` required an older `starlette`,
   while the `mcp` library required a newer one.
   *Fix:* bumped FastAPI to a version whose range overlaps (`>=0.115.6`), letting
   pip find one `starlette` that satisfies both.
   *Lesson:* transitive dependency conflicts are resolved by finding compatible
   version ranges, not forcing installs.

2. **Next.js security advisory.**
   `npm install` warned that `next@14.2.5` had a vulnerability.
   *Fix:* upgraded to the patched `14.2.35` on the same major line (no breaking
   changes), rather than `npm audit fix --force` (which could jump to Next 15).
   *Lesson:* patch within your version line to stay safe without breaking things.

3. **pip "file not found" / wrong environment.**
   Ran `pip install -r requirements.txt` from the wrong folder and without the
   virtual environment active ("Defaulting to user installation").
   *Fix:* `cd backend`, `source .venv/bin/activate`, then install.
   *Lesson:* always activate your venv; the `(.venv)` prefix confirms it.

4. **Anthropic model 404.**
   The API rejected the model name `claude-3-5-sonnet-latest` (that alias isn't
   valid on the current API).
   *Fix:* made the model configurable via `ANTHROPIC_MODEL` (default
   `claude-sonnet-5`) and added error handling so a bad model shows a readable
   message instead of crashing the stream.
   *Lesson:* never hardcode external identifiers that can change; make them
   config, and fail gracefully.

5. **Docker port clash (5432 already in use).**
   A local Postgres was already using host port 5432, so the container couldn't
   bind it.
   *Fix:* published the container DB on host port **5433** (`5433:5432`). The
   backend still reaches the DB internally at `db:5432`.
   *Lesson:* container-to-container traffic uses the internal network; only the
   *published* host port can clash.

6. **"The terminal is stuck."**
   `docker compose up` (foreground) streams logs and never returns the prompt.
   *Fix:* run detached with `docker compose up -d`, or use a second terminal.
   *Lesson:* foreground vs detached processes.

7. **Got the stub reply / leaked prompt.**
   The Docker backend had no API key (it reads `infra/.env`, not `backend/.env`),
   so it used the stub — which also echoed the internal prompt.
   *Fix:* put the key in `infra/.env`; cleaned the stub so it never echoes the
   constructed prompt.
   *Lesson:* know exactly which env file each runtime reads; don't leak internal
   prompts to users.

---

## Part 7 — Interview questions (with model answers)

Grouped by area. Difficulty: 🟢 beginner, 🟡 intermediate, 🔴 advanced.

### A. Project & general

**🟢 Q: Describe your project in two minutes.**
A: It's an adaptive tutoring chatbot. A user picks a topic and the bot teaches it
step by step, grounding explanations in real documentation fetched through MCP,
generating exercises, and tracking mastery in a database so lessons adapt. The
stack is a Next.js frontend, a FastAPI backend with a custom agent loop,
PostgreSQL with pgvector for storage and semantic search, and Docker Compose to
run it all. It's designed so new documentation sources are added as configuration
rather than code.

**🟡 Q: What makes it more than a wrapper around an LLM?**
A: Three things: retrieval grounding (it teaches from fetched docs, not just model
memory), stateful learner modeling (a concept graph plus per-user mastery drives
what's taught next), and a pluggable architecture (an MCP registry table lets you
add sources without touching the core loop). Plus it's fully containerized.

**🟡 Q: If you had two more weeks, what would you add?**
A: Wire the real CUDA MCP retrieval with citations, seed a full CUDA concept
graph, implement the quiz/grade cycle with mastery updates, add a progress
dashboard, and populate the pgvector retrieval cache to cut latency and cost.

### B. Backend / FastAPI

**🟢 Q: Why FastAPI over Flask or Django?**
A: FastAPI is async-native, which suits streaming LLM responses; it gives
automatic request validation via Pydantic and auto-generated API docs. Django is
heavier and synchronous at its core; Flask would need more manual wiring for
async, validation, and docs.

**🟡 Q: What is `pydantic-settings` doing in your config?**
A: It loads configuration from environment variables (and a `.env` file) into a
typed object, with validation and defaults. This keeps secrets out of code and
catches misconfiguration early.

**🟡 Q: How does your streaming endpoint work?**
A: `POST /sessions/{id}/message` returns a `StreamingResponse` with media type
`text/event-stream`. An async generator yields Server-Sent Events: each token is
JSON-encoded inside a `data:` frame, and a final `data: [DONE]` frame ends the
stream. Wrapping generation in try/except/finally guarantees the stream always
closes cleanly.

**🔴 Q: Why JSON-encode each token instead of sending raw text?**
A: SSE frames are separated by a blank line (`\n\n`). If a raw token contained a
blank line, it would corrupt the framing and split one message into two. JSON
encoding escapes newlines, so any token is safe. We verified this round-trips
exactly, including the newline edge case.

### C. Databases, SQL & pgvector

**🟢 Q: Why a relational database here?**
A: The data is highly related — users have mastery states per concept; concepts
have prerequisites; sessions have messages. SQL joins and foreign keys model this
cleanly and enforce integrity.

**🟡 Q: What is pgvector and why use it?**
A: It's a PostgreSQL extension adding a `vector` column type and similarity
search. We store embeddings of retrieved docs so we can find the most
semantically similar cached results — semantic search inside the same database,
avoiding a separate vector store.

**🟡 Q: What's an embedding, simply?**
A: A numeric representation of meaning. Text with similar meaning maps to nearby
vectors, so "closeness" in vector space ≈ similarity in meaning.

**🔴 Q: What is the `ivfflat` index you created?**
A: An approximate-nearest-neighbor index for vector columns. Exact nearest-
neighbor search is slow at scale; `ivfflat` groups vectors into lists and
searches the most promising ones, trading a little accuracy for a large speed
gain. It's created with a vector operator class (e.g., cosine distance).

**🟡 Q: You keep SQL and ORM models both. Why, and what's the risk?**
A: The SQL migration is the source of truth for schema (precise control over
extensions, enums, indexes); the SQLAlchemy models give typed queries in Python.
The risk is drift — they must be kept in sync manually. A migration tool like
Alembic would automate this as the project grows.

### D. RAG, MCP & LLM orchestration

**🟢 Q: What is RAG and why does it matter?**
A: Retrieval-Augmented Generation: fetch relevant documents and include them in
the prompt so the model answers from real sources instead of only its training.
It reduces hallucinations and lets the app use private or up-to-date data.

**🟡 Q: What is MCP and how do you use it?**
A: Model Context Protocol is a standard interface for connecting AI apps to
external tools and data. In our design, the agent asks a `Retriever` for docs; a
registry of MCP servers decides which server(s) answer. New sources are added as
registry rows, not code.

**🟡 Q: Walk me through your agent loop.**
A: For one turn: load context, pick the next concept (currently stubbed, later
driven by mastery + prerequisites), retrieve grounding docs via the MCP layer,
build a prompt combining tutor instructions + docs + the learner's message, then
stream the model's reply token by token.

**🔴 Q: Why not use LangChain?**
A: For this project I wanted the orchestration to be explicit and explainable,
and to avoid heavy dependencies and hidden control flow. A custom loop makes the
retrieve/teach/grade steps transparent. LangChain is great for rapid assembly,
but here clarity and control were the priority.

**🔴 Q: How does your design "scale with more MCPs based on user preference"?**
A: The `mcp_registry` table stores each server with the topics it covers, an
enabled flag, and a priority. A topic router queries this table to pick relevant,
enabled servers per request. Adding or toggling sources is data, not code, and
per-user preferences can filter the candidate list.

### E. Streaming & frontend

**🟢 Q: Why stream responses at all?**
A: LLMs generate text gradually; streaming shows tokens as they arrive, which
feels far more responsive than waiting for the whole answer.

**🟡 Q: Why `fetch` + a stream reader instead of `EventSource`?**
A: `EventSource` only supports GET requests. We need to POST the user's message
(with a body), so we use `fetch` and read the response body as a stream, parsing
SSE frames ourselves.

**🟡 Q: What does `NEXT_PUBLIC_` mean in Next.js env vars?**
A: Variables prefixed with `NEXT_PUBLIC_` are inlined into the browser bundle at
build time and are readable client-side. Without the prefix, a variable stays
server-only. That's why it's set as a build argument in the frontend Dockerfile.

### F. Docker & DevOps

**🟢 Q: What problem does Docker solve here?**
A: It packages each service with its exact dependencies so it runs the same on any
machine, and Compose starts the whole multi-service system with one command.

**🟡 Q: How does the database get its schema in Docker?**
A: The official Postgres image runs any SQL in `/docker-entrypoint-initdb.d/` on
first startup. We mount our `infra/db/init/` folder there, so `001_init.sql`
executes automatically when the database is first created.

**🟡 Q: Explain the port clash you fixed.**
A: The container tried to publish Postgres on host port 5432, but a local Postgres
already held it. I remapped the published port to `5433:5432`. The backend still
connects internally over Compose's network at `db:5432`; only the host-facing port
changed.

**🔴 Q: Why a multi-stage build for the frontend?**
A: The first stage installs dev dependencies and builds the app; the second stage
copies only the build output and production dependencies into a smaller runtime
image. This yields a lean, faster-to-ship container without build tooling inside.

**🟡 Q: Why does `depends_on` alone not guarantee the DB is ready?**
A: `depends_on` controls start order, not readiness. A container can be "started"
but the database still initializing. We added a `healthcheck` (`pg_isready`) and
made the backend wait for the DB to be *healthy*, not just started.

### G. Security & good practices

**🟢 Q: How do you keep secrets out of Git?**
A: `.env` files hold secrets and are listed in `.gitignore`, so they're never
committed. Example files (`.env.example`) document required variables without
real values.

**🟡 Q: Where does the Dockerized backend read its API key from, and why did the
stub appear?**
A: Under Compose it reads `infra/.env` (passed in via the compose file). The stub
appeared because that file didn't have the key yet, so the app fell back to the
safe stub. Adding the key to `infra/.env` and restarting fixed it.

### H. System design / scaling (stretch)

**🔴 Q: How would you scale this to thousands of users?**
A: Run multiple stateless backend replicas behind a load balancer (state lives in
Postgres, so replicas are interchangeable); add read replicas or connection
pooling for the DB; cache retrievals in pgvector to cut LLM/MCP calls; add rate
limiting and per-tenant isolation; and move long tasks to a queue if needed.

**🔴 Q: How would you evaluate teaching quality?**
A: Build a golden set of questions with expected cited sources to catch grounding
regressions; track exercise pass rates and mastery progression; and log
retrieval hit rates and latency. Add human spot-checks for correctness.

---

## Part 8 — Glossary (quick reference)

- **API endpoint:** a specific URL + method the backend responds to.
- **Async:** code that can handle other work while waiting (e.g., for the LLM),
  key to efficient streaming.
- **Container / image:** a running instance / the built template it runs from.
- **Embedding:** numeric meaning-vector of text.
- **Environment variable:** a setting supplied from outside the code (often via
  `.env`).
- **Foreign key:** a column that references a row in another table (enforces
  relationships).
- **Hallucination:** an LLM confidently stating something false.
- **LLM:** large language model (Claude here).
- **Migration:** a versioned change to the database schema.
- **ORM:** object-relational mapper (SQLAlchemy) — query the DB with objects.
- **RAG:** retrieval-augmented generation.
- **SSE:** server-sent events, a one-way stream from server to browser.
- **Stub:** a stand-in implementation used until the real one is wired.
- **Token:** a chunk of text the model generates (roughly a word-piece).

---

## Part 9 — How to run it (cheat sheet)

**Everything at once (Docker):**
```bash
cd infra
cp .env.example .env         # add ANTHROPIC_API_KEY (blank = stub tutor)
docker compose up -d --build # start in background
# open http://localhost:3000 ; API at http://localhost:8000/health
docker compose logs -f       # watch logs
docker compose down          # stop
```

**Backend only (no Docker):**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend only (no Docker):**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                  # http://localhost:3000
```

---

*Tip for interviews: don't just recite features — tell the story of a decision or
a bug (Part 5 and Part 6). Explaining a trade-off or a fix you made is far more
convincing than listing technologies.*

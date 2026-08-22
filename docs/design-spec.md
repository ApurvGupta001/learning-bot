# Personalized Learning Bot — Design Specification

**Version:** 1.0  ·  **Date:** 2026-08-22  ·  **Status:** Approved for build

An MCP-powered adaptive learning chatbot. A learner picks a topic (starting with CUDA), and the bot teaches it step-by-step — grounding every explanation in *real* documentation fetched live through Model Context Protocol (MCP) servers, generating exercises, grading answers, and tracking mastery so it can adapt what it teaches next.

---

## 1. Goals & Non-Goals

### Goals
- Deliver an adaptive **teach → check → adapt** loop, not a one-shot Q&A bot.
- Ground every concept explanation in real docs via the **NVIDIA CUDA MCP server** (no hallucinated APIs).
- Model per-learner knowledge state so teaching order and difficulty adapt to the individual.
- Design the MCP layer so **new MCP servers plug in via config**, with zero changes to the agent loop.
- Ship a clean, demoable product in ~2 weeks that is easy to explain in an interview.

### Non-Goals (v1)
- Multi-topic breadth — one topic (CUDA) is fully seeded; others are proven via a stub.
- Production-grade auth/billing — a single demo user or minimal JWT is enough.
- Fine-tuning or training models — this is orchestration + retrieval + state, by design.

---

## 2. Why This Project (Interview Positioning)

Most candidates present a RAG chatbot. This project layers three harder, distinct competencies:

1. **Custom agent loop** — a hand-written orchestration loop (no LangChain), so every decision is explainable in an interview.
2. **MCP tool orchestration** — real external grounding through a standardized protocol, with a pluggable registry.
3. **Stateful learner modeling** — a concept graph + mastery tracking that makes the bot *adaptive* rather than linear.

Together these signal product thinking and systems design, not "LLM glue." The design intentionally echoes real askme360 themes (LLM orchestration, document grounding, workflow/routing) without copying the product.

---

## 3. Personas & Core User Flow

**Primary persona:** a self-directed learner (e.g., an engineer learning CUDA) who wants structured, trustworthy, hands-on instruction.

**Core flow:**
1. Learner selects a topic and (optionally) a starting level.
2. Bot picks the next concept from the topic's concept graph based on the learner's current state.
3. Bot fetches supporting docs via the relevant MCP server(s) and explains the concept with citations.
4. Bot generates a short exercise (conceptual question or code snippet).
5. Learner answers; bot grades and gives targeted feedback tied to specific doc sections.
6. Bot updates the learner's mastery state and loops to the next concept.
7. Learner can view a progress dashboard (concept map + mastery levels) at any time.

---

## 4. Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│  Next.js (chat UI + progress dashboard)                      │
└───────────────┬────────────────────────────────────────────┘
                │  HTTP + SSE (streamed tokens)
┌───────────────▼────────────────────────────────────────────┐
│  FastAPI backend                                            │
│                                                            │
│   Agent Loop (custom):                                      │
│     plan → retrieve → teach → quiz → grade → update state    │
│         │             │              │                      │
│         │             ▼              ▼                      │
│         │      MCP Client Layer   Learner State Service      │
│         │             │              │                      │
│         │      ┌──────▼───────┐      ▼                      │
│         │      │ MCP Registry │   Postgres                  │
│         │      │  (config)    │   + pgvector (retrieval cache)│
│         │      └──────┬───────┘                             │
│         │             ▼                                     │
│         │      [ NVIDIA CUDA MCP ]  (+ future MCP servers)   │
└─────────┴───────────────────────────────────────────────────┘
```

The agent loop never talks to a specific MCP server directly. It asks the **MCP Client Layer** for "docs relevant to concept X," and the **registry + topic router** decide which registered server(s) to call. This indirection is the scalability seam.

---

## 5. Component Design

### 5.1 Agent Loop (custom orchestration)
A deterministic state machine wrapping LLM calls. Pseudocode:

```python
def teaching_turn(user_id, topic_id, user_input=None):
    state = state_service.load(user_id, topic_id)

    # 1. Decide the next pedagogical action
    concept = pick_next_concept(state)           # graph + mastery aware
    intent  = classify_intent(user_input, state) # question | answer | continue

    # 2. Retrieve grounding (via MCP layer, not a specific server)
    docs = mcp.retrieve(topic_id, concept.query_terms)

    # 3. Act
    if intent == "answer":
        grade = llm_grade(user_input, concept, docs)
        state_service.record_attempt(user_id, concept, grade)
        reply = feedback_from(grade, docs)       # cites doc sections
    else:
        reply = llm_teach(concept, docs)         # explanation + citations
        exercise = llm_make_exercise(concept, docs)
        reply += exercise

    # 4. Persist + stream
    state_service.save(state)
    return stream(reply)
```

Key point for interviews: the loop is explicit and inspectable. You choose when to retrieve, when to grade, and how state changes — no framework hides it.

### 5.2 MCP Client Layer + Registry (the scalability core)
- Uses the official **Python MCP SDK** as a client.
- Each MCP server is described by a **registry entry** (stored in `mcp_registry`):
  - `name`, `endpoint`/launch command, `auth_ref`
  - `topics` it covers (e.g., `["cuda", "gpu"]`)
  - discovered `tool_schema` (fetched on registration)
  - `enabled`, `priority`
- A **topic router** maps the current concept's topic → candidate MCP servers, calls their search tools, and merges/deduplicates results.
- **Adding a new MCP later** = insert a registry row + credentials + list its topics. The agent loop is untouched.

### 5.3 Learner State Service
- Reads/writes mastery state and attempt history.
- Exposes `pick_next_concept(state)` using the concept graph: never teach a concept whose prerequisites aren't yet "learning/mastered"; prefer concepts just past the learner's frontier.
- Mastery ladder: `unseen → learning → mastered` (promotion after N correct attempts; demotion on repeated misses).

### 5.4 Retrieval Cache (pgvector)
- MCP results are embedded and cached keyed by `(topic, normalized_query)`.
- Cuts latency and repeat MCP calls; on cache hit, skip the network round-trip.

### 5.5 Frontend (Next.js)
- Chat view with SSE token streaming and inline citation chips.
- Progress dashboard: concept graph visualization with per-node mastery coloring.
- Topic picker; simple session history.

---

## 6. Data Model

```
users(id, name, created_at)

topics(id, slug, title, description)

concepts(
  id, topic_id → topics,
  slug, title, summary,
  prerequisites (int[]  → concept ids),
  order_hint
)

learner_concept_state(
  user_id → users, concept_id → concepts,
  mastery ENUM(unseen, learning, mastered),
  attempts int, correct int,
  last_seen_at,
  PRIMARY KEY (user_id, concept_id)
)

sessions(id, user_id, topic_id, started_at)
messages(id, session_id, role, content, citations jsonb, created_at)

mcp_registry(
  id, name, endpoint, auth_ref,
  topics text[], tool_schema jsonb,
  enabled bool, priority int
)

retrieval_cache(
  id, topic, query_norm, embedding vector,
  payload jsonb, source_mcp, created_at
)
```

The `concepts.prerequisites` array is what turns a flat list of topics into an adaptive **concept graph**.

---

## 7. API Surface (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/topics` | List available topics |
| `POST` | `/sessions` | Start a learning session for a topic |
| `POST` | `/sessions/{id}/message` | Send a message; returns SSE stream |
| `GET`  | `/progress/{user_id}/{topic_id}` | Concept map + mastery for dashboard |
| `GET`  | `/mcp/registry` | List registered MCP servers (admin) |
| `POST` | `/mcp/registry` | Register a new MCP server (admin) |

---

## 8. Build Phases (2 Weeks)

**Phase 1 — Foundations (days 1–3):** repo scaffold; FastAPI + Next.js wired with SSE; Postgres schema + migrations; bare agent loop calling the LLM with no tools.

**Phase 2 — MCP integration (days 4–6):** MCP client layer; register + connect the NVIDIA CUDA MCP; wrap its search tools; prove grounded answers with citations. *Technical core.*

**Phase 3 — Learning engine (days 7–10):** seed the CUDA concept graph; implement teach/quiz/grade cycle; learner-state updates; `pick_next_concept` logic.

**Phase 4 — UX + scale seams (days 11–13):** progress dashboard; registry-driven topic router with a **stub second MCP** to prove pluggability; pgvector retrieval caching.

**Phase 5 — Polish (day 14):** README + architecture diagram; seed data; demo script; deploy (Vercel + Railway/Fly).

---

## 9. Tech Stack

- **Frontend:** Next.js / TypeScript, SSE for streaming.
- **Backend:** FastAPI / Python; custom agent loop over the Anthropic or OpenAI SDK.
- **MCP:** official Python MCP SDK (client); NVIDIA CUDA MCP server first.
- **Data:** Postgres + pgvector.
- **Infra:** Docker Compose for local dev; Vercel (web) + Railway/Fly (API + DB) for deploy.

---

## 10. Scalability & Extensibility

- **More MCPs on demand:** registry + topic router means new servers (GitHub, Brave Search, networking docs) are config additions. This is the "scale with more MCPs based on user preference" requirement.
- **User-preference routing:** a learner can enable/disable MCP sources per topic; the router filters candidates by `enabled` + user preference.
- **More topics:** each new topic = a concept graph + at least one MCP that covers it.
- **Caching & cost control:** pgvector cache reduces repeat MCP/LLM calls; priorities let cheaper/faster sources win ties.
- **Horizontal scale:** stateless API workers; state lives in Postgres; MCP calls are per-request and cacheable.

---

## 11. Testing & Quality

- Unit tests for `pick_next_concept` (prerequisite ordering, promotion/demotion).
- Contract tests for the MCP client layer against a mock MCP server (proves pluggability without the real network).
- Golden-set eval: a handful of CUDA questions with expected cited sources, to catch grounding regressions.
- Manual demo script that walks the full teach→quiz→grade→adapt loop.

---

## 12. Risks & Mitigations

- **MCP server availability/latency** → retrieval cache + graceful fallback message.
- **Grading reliability** (LLM grading is fuzzy) → structured rubric prompts + conceptual-answer tolerance; keep exercises small.
- **Scope creep** → guardrails in §1 Non-Goals; second MCP stays a stub in v1.

---

## 13. Interview Talking Points (cheat sheet)

- "I built the agent loop by hand so I could control retrieval, grading, and state transitions — no framework hiding the logic."
- "MCP integration sits behind a registry + router, so adding a new documentation source is a config change, not a code change."
- "Teaching is driven by a concept graph with prerequisites, so the bot adapts order and difficulty to the learner's mastery state."
- "Retrieval is cached in pgvector to cut latency and cost on repeated concepts."
- "This reflects real enterprise AI patterns I worked with — LLM orchestration, document grounding, and rule/route-based flow — rebuilt cleanly from scratch."

# PRD — Personalized Learning Bot

**Product Requirements Document** · v1.0 · Status: active build

## 1. Problem & vision

Self-directed learners struggle to study technical topics because generic
chatbots hallucinate, don't teach in a structured order, and don't remember what
the learner already knows. The Personalized Learning Bot is an adaptive tutor
that teaches a topic step by step, grounds every explanation in **real
documentation** (fetched via MCP), generates exercises, grades them, and tracks
mastery so lessons adapt to the individual.

First topic: **CUDA** (NVIDIA GPU programming). The architecture is topic-agnostic
so more topics/doc-sources are added later.

## 2. Target users

| Persona | Description | Primary need |
|---|---|---|
| Self-taught engineer | Learning a new technical skill (e.g., CUDA) on their own | Structured, trustworthy, hands-on lessons |
| Student | Supplementing coursework | Adaptive practice + explanations grounded in official docs |
| Career switcher (primary) | Building portfolio skills / prepping for interviews | A credible, well-architected learning tool + practice |

## 3. Goals & non-goals

**Goals**
- Adaptive **teach → check → adapt** loop, not one-shot Q&A.
- Ground explanations in real docs via MCP; cite sources.
- Model per-learner mastery to drive what's taught next.
- Pluggable design: add MCP doc-sources via configuration, not code.
- Run the whole system with one command (Docker Compose).

**Non-goals (v1)**
- Multiple fully-seeded topics (CUDA first; others proven via a stub).
- Production-grade auth/billing/multi-tenant SSO.
- Model fine-tuning (this is orchestration + retrieval + state).

## 4. Features

### Must-have (MVP)
- **F1 — Topic selection:** pick a topic to learn.
- **F2 — Streaming chat tutor:** ask questions, get lessons streamed live.
- **F3 — Doc-grounded answers (RAG via MCP):** fetch real docs and teach from
  them with citations. *(Retriever interface built; real CUDA MCP pending.)*
- **F4 — Concept graph:** a syllabus of concepts with prerequisites. *(Schema
  built; seed data pending.)*
- **F5 — Mastery tracking:** record attempts/correctness per concept, promote/
  demote mastery. *(Schema built; logic pending.)*
- **F6 — Exercises + grading:** generate an exercise, grade the answer, give
  targeted feedback. *(Pending — learning-engine phase.)*

### Should-have
- **F7 — Progress dashboard:** visualize the concept graph + mastery.
- **F8 — MCP registry admin:** enable/disable/prioritize doc-sources.
- **F9 — Retrieval cache:** embed + cache fetched docs (pgvector) to cut latency.

### Could-have (later)
- **F10 — Multiple topics** with their own concept graphs.
- **F11 — Per-user MCP preferences** (choose which doc-sources to use).
- **F12 — Auth & multi-user** history.

## 5. User stories (samples)

- As a learner, I can pick **CUDA** and ask "teach me threads," and see a lesson
  stream in, so learning feels responsive.
- As a learner, I get answers grounded in official docs **with citations**, so I
  trust them.
- As a learner, the bot teaches prerequisites first, so I'm never lost.
- As a learner, I can see which concepts I've mastered, so I know my progress.

## 6. Success metrics
- Exercise pass rate and mastery progression per learner.
- Retrieval **grounding rate** (answers backed by fetched docs) and cache hit rate.
- Streaming latency to first token.
- Qualitative: lessons are correct, ordered, and cited.

## 7. Constraints & assumptions
- LLM: Anthropic Claude (model via `ANTHROPIC_MODEL`, default `claude-sonnet-5`).
- Runs with **no API key** using a safe stub (for demos/tests).
- Postgres + pgvector is the single datastore (relational + vectors).
- Secrets live in `.env` files, never committed.

## 8. Current status (high level)
MVP scaffold complete: streaming chat works end-to-end (stub or real LLM);
schema, frontend, agent loop, MCP interface, and Docker Compose are in place.
Pending: real CUDA MCP retrieval, concept-graph seed, quiz/grade + mastery,
progress dashboard. See `Phases.md` and `Memory.md`.

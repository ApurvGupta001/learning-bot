"""The custom agent loop.

One teaching turn: pick a concept -> retrieve grounding via MCP -> teach (stream).
Grading and learner-state updates are added in the learning-engine step; the
seams (concept selection, doc grounding) are already here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.agent.llm import LLM
from app.mcp.client import RetrievedDoc, Retriever

SYSTEM_PROMPT = (
    "You are a patient, precise tutor. Teach ONE concept at a time in plain "
    "language, then pose a short exercise. Ground your explanation in the "
    "provided documentation and cite it when you use it. If no docs are "
    "provided, say what you'd look up and proceed carefully."
)


def _format_docs(docs: list[RetrievedDoc]) -> str:
    if not docs:
        return "(no grounding docs available yet)"
    lines = []
    for i, d in enumerate(docs, 1):
        src = f" [{d.url}]" if d.url else ""
        lines.append(f"{i}. {d.title}: {d.snippet}{src}")
    return "\n".join(lines)


async def run_turn(
    *,
    topic: str,
    user_input: str,
    llm: LLM,
    retriever: Retriever,
    concept_title: str = "Introduction",
) -> AsyncIterator[str]:
    """Yield the assistant's reply token-by-token for one turn.

    `concept_title` is a stub for now; the learning-engine step replaces it with
    `pick_next_concept()` driven by the learner's mastery state + concept graph.
    """
    docs = await retriever.retrieve(topic, user_input)
    context = _format_docs(docs)

    messages = [
        {
            "role": "user",
            "content": (
                f"Topic: {topic}\n"
                f"Concept to teach: {concept_title}\n"
                f"Documentation:\n{context}\n\n"
                f"Learner says: {user_input}"
            ),
        }
    ]

    async for token in llm.stream(SYSTEM_PROMPT, messages):
        yield token

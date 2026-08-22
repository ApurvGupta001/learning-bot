"""Session + chat routes.

`POST /sessions/{id}/message` streams the assistant reply as Server-Sent Events.
Each token is JSON-encoded inside a `data:` frame (so tokens containing newlines
can't break SSE framing); a final `data: [DONE]` frame closes the stream.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.llm import LLM
from app.agent.loop import run_turn
from app.mcp.client import build_retriever
from app.schemas import MessageIn

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Built once at import; cheap and stateless. (Swap for DI if you need per-request.)
_llm = LLM()
_retriever = build_retriever()


def _sse(data: str) -> bytes:
    return f"data: {data}\n\n".encode()


@router.post("/{session_id}/message")
async def post_message(session_id: str, body: MessageIn, topic: str = "cuda"):
    """Stream a tutor reply for one learner message.

    Persistence of messages + learner-state updates are added in the
    learning-engine step; this endpoint focuses on the streaming agent turn.
    """

    async def gen() -> AsyncIterator[bytes]:
        try:
            async for token in run_turn(
                topic=topic,
                user_input=body.content,
                llm=_llm,
                retriever=_retriever,
            ):
                yield _sse(json.dumps(token))
        except Exception as exc:  # noqa: BLE001 - always close the stream cleanly
            yield _sse(json.dumps(f"\n[server error: {type(exc).__name__}: {exc}]"))
        finally:
            yield _sse("[DONE]")

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

"""LLM wrapper with streaming.

If an Anthropic API key is configured, stream from the real model. Otherwise
fall back to a deterministic stub stream so the whole app runs (and the chat
UI streams) with zero credentials — useful for local dev, tests, and demos.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.config import settings


class LLM:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self._client = None
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=self.api_key)
            except Exception:
                # SDK missing/incompatible -> degrade to stub rather than crash.
                self._client = None

    @property
    def is_stub(self) -> bool:
        return self._client is None

    async def stream(
        self, system: str, messages: list[dict], max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        if self._client is None:
            async for tok in self._stub_stream(messages):
                yield tok
            return

        try:
            async with self._client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as exc:  # noqa: BLE001 - surface a readable message, don't crash the stream
            yield (
                f"\n[LLM error: {type(exc).__name__}: {exc}]\n"
                f"(Check ANTHROPIC_MODEL='{self.model}' is a valid model ID and your API key.)"
            )

    async def _stub_stream(self, messages: list[dict]) -> AsyncIterator[str]:
        last = messages[-1]["content"] if messages else ""
        text = (
            "(stub tutor) I received your message. The real Anthropic model and "
            "CUDA MCP grounding get wired in the next step; for now this proves the "
            "streaming path works end to end.\n\n"
            f"You said: {last}"
        )
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.01)

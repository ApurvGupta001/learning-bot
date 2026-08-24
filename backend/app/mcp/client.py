"""Retriever interface + implementations.

`Retriever` is the single abstraction the agent loop depends on. We ship:
- `StubRetriever` (returns nothing; app runs with no MCP configured), and
- `CudaMCPRetriever` (connects to the NVIDIA CUDA MCP server, auto-discovers its
  search tool, calls it, and maps results to RetrievedDoc).

Adding more servers later means registering them (mcp_registry) and letting the
router pick — no change to the agent loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDoc:
    """A single grounding snippet returned from an MCP server."""

    title: str
    snippet: str
    url: str | None = None
    source: str | None = None  # which MCP server produced it


@runtime_checkable
class Retriever(Protocol):
    """Anything the agent loop can pull grounding docs from."""

    async def retrieve(self, topic: str, query_terms: str) -> list[RetrievedDoc]:
        ...


class StubRetriever:
    """No-op retriever. Lets the app run before any MCP server is configured."""

    async def retrieve(self, topic: str, query_terms: str) -> list[RetrievedDoc]:
        return []


def _coerce_docs(result: Any, source: str, max_docs: int = 5) -> list[RetrievedDoc]:
    """Map an MCP `call_tool` result into RetrievedDoc objects.

    MCP servers differ in shape, so we try two paths:
    1. `structuredContent` with a list of result dicts (title/url/snippet-ish).
    2. Fallback: the `content` text blocks, each becomes a doc snippet.

    Pulled out as a pure function so it can be unit-tested without a network.
    """
    docs: list[RetrievedDoc] = []

    structured = getattr(result, "structuredContent", None)
    if structured is None and isinstance(result, dict):
        structured = result.get("structuredContent")

    items = None
    if isinstance(structured, dict):
        for key in ("results", "documents", "matches", "items", "data"):
            value = structured.get(key)
            if isinstance(value, list):
                items = value
                break
    elif isinstance(structured, list):
        items = structured

    if items:
        for it in items[:max_docs]:
            if isinstance(it, dict):
                title = it.get("title") or it.get("name") or it.get("heading") or "CUDA doc"
                snippet = (
                    it.get("snippet")
                    or it.get("text")
                    or it.get("content")
                    or it.get("body")
                    or ""
                )
                url = it.get("url") or it.get("link") or it.get("source")
                docs.append(
                    RetrievedDoc(
                        title=str(title),
                        snippet=str(snippet)[:800],
                        url=str(url) if url else None,
                        source=source,
                    )
                )
        if docs:
            return docs

    # Fallback: plain text content blocks.
    content = getattr(result, "content", None)
    if content is None and isinstance(result, dict):
        content = result.get("content")
    for block in content or []:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            docs.append(
                RetrievedDoc(title="CUDA doc", snippet=str(text)[:800], source=source)
            )
        if len(docs) >= max_docs:
            break

    return docs


_QUERY_ARG_CANDIDATES = (
    "query", "q", "question", "search", "search_query", "text", "prompt", "input"
)


def _pick_query_arg(input_schema: Any, preferred: str = "query") -> str:
    """Choose the tool's query argument name from its JSON input schema.

    Prefers the configured name, then common synonyms, then the first string
    property. Falls back to `preferred` if no schema is available.
    """
    props = {}
    if isinstance(input_schema, dict):
        props = input_schema.get("properties") or {}
    if not props:
        return preferred

    ordered = [preferred] + [c for c in _QUERY_ARG_CANDIDATES if c != preferred]
    for name in ordered:
        if name in props:
            return name
    for name, spec in props.items():
        if isinstance(spec, dict) and spec.get("type") == "string":
            return name
    for name in props:  # last resort: first property of any type
        return name
    return preferred


class CudaMCPRetriever:
    """Retriever backed by the NVIDIA CUDA MCP server.

    We don't hardcode the tool name: on each call we (optionally) discover the
    server's tools and pick the search tool, then call it with the query. This
    keeps us resilient to the server's exact schema and is easy to point at any
    MCP search server.
    """

    SOURCE = "cuda-mcp"

    def __init__(
        self,
        endpoint: str,
        *,
        tool_name: str = "",
        query_arg: str = "query",
        api_key: str = "",
        transport: str = "http",
        max_docs: int = 5,
    ) -> None:
        self.endpoint = endpoint
        self.tool_name = tool_name
        self.query_arg = query_arg
        self.api_key = api_key
        self.transport = transport  # "http" (streamable) or "sse"
        self.max_docs = max_docs

    async def retrieve(self, topic: str, query_terms: str) -> list[RetrievedDoc]:
        # Never let a retrieval failure crash a lesson; degrade to "no docs".
        try:
            return await self._search(query_terms)
        except Exception as exc:  # noqa: BLE001
            logger.warning("CUDA MCP retrieval failed (%s): %s", type(exc).__name__, exc)
            return []

    async def _search(self, query: str) -> list[RetrievedDoc]:
        from mcp import ClientSession

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None

        if self.transport == "sse":
            from mcp.client.sse import sse_client

            ctx = sse_client(self.endpoint, headers=headers)
        else:
            from mcp.client.streamable_http import streamablehttp_client

            ctx = streamablehttp_client(self.endpoint, headers=headers)

        async with ctx as streams:
            # streamable_http yields (read, write, get_session_id); sse yields (read, write)
            read, write = streams[0], streams[1]
            async with ClientSession(read, write) as session:
                await session.initialize()
                name, schema = await self._select_tool(session)
                arg = _pick_query_arg(schema, self.query_arg)
                logger.info("CUDA MCP: calling tool %r with arg %r", name, arg)
                result = await session.call_tool(name, {arg: query})
                return _coerce_docs(result, source=self.SOURCE, max_docs=self.max_docs)

    async def _select_tool(self, session: Any) -> tuple[str, Any]:
        """Return (tool_name, input_schema). Auto-discovers if not configured."""
        listed = await session.list_tools()
        tools = getattr(listed, "tools", []) or []

        def pair(t: Any) -> tuple[str, Any]:
            return t.name, getattr(t, "inputSchema", None)

        if self.tool_name:
            for t in tools:
                if t.name == self.tool_name:
                    return pair(t)
            return self.tool_name, None  # configured but not listed; try anyway
        for t in tools:
            if "search" in getattr(t, "name", "").lower():
                return pair(t)
        if tools:
            return pair(tools[0])
        raise RuntimeError("CUDA MCP server exposes no tools to call")


def build_retriever() -> Retriever:
    """Factory: pick a retriever from config.

    Returns a CudaMCPRetriever when CUDA_MCP_URL is set, else a StubRetriever.
    Later this can read the mcp_registry table and fan out to multiple servers.
    """
    from app.config import settings

    if settings.cuda_mcp_url:
        return CudaMCPRetriever(
            settings.cuda_mcp_url,
            tool_name=settings.cuda_mcp_tool,
            query_arg=settings.mcp_query_arg,
            api_key=settings.cuda_mcp_api_key,
            transport=settings.cuda_mcp_transport,
        )
    return StubRetriever()

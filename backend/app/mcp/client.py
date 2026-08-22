"""Retriever interface + implementations.

`Retriever` is the single abstraction the agent loop depends on. Today we ship
a `StubRetriever` (returns nothing, so the app runs with no MCP configured) and
a `CudaMCPRetriever` placeholder wired in the next step against the NVIDIA CUDA
MCP server. Adding more servers later means registering them and letting the
router pick — no change to the agent loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


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


class CudaMCPRetriever:
    """Placeholder for the NVIDIA CUDA MCP server (wired in the next step).

    The next step will: open an MCP client session to `endpoint`, call the
    server's search tool with `query_terms`, and map results into RetrievedDoc.
    """

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    async def retrieve(self, topic: str, query_terms: str) -> list[RetrievedDoc]:
        # TODO(step: MCP integration): call the CUDA MCP search tool here.
        raise NotImplementedError("CUDA MCP integration lands in the next step.")


def build_retriever() -> Retriever:
    """Factory: choose a retriever from config.

    For now returns a StubRetriever unless a CUDA MCP endpoint is configured.
    Later this reads the mcp_registry table and returns a composite retriever
    that fans out to all servers matching the topic.
    """
    from app.config import settings

    if settings.cuda_mcp_url:
        return CudaMCPRetriever(settings.cuda_mcp_url)
    return StubRetriever()

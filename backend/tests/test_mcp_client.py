"""Contract tests for MCP result parsing.

These test the pure `_coerce_docs` mapping without any network or MCP server,
proving the retriever handles the shapes an MCP `call_tool` result can take.

Run:  cd backend && python -m pytest        (or: python tests/test_mcp_client.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mcp.client import (  # noqa: E402
    RetrievedDoc,
    StubRetriever,
    _coerce_docs,
    _pick_query_arg,
)


class _Block:
    def __init__(self, text: str) -> None:
        self.text = text


class _StructuredResult:
    structuredContent = {
        "results": [
            {
                "title": "Thread Hierarchy",
                "snippet": "Threads are grouped into blocks...",
                "url": "https://docs.nvidia.com/cuda/#thread-hierarchy",
            },
            {
                "name": "Kernels",
                "text": "A kernel is defined using __global__...",
                "link": "https://docs.nvidia.com/cuda/#kernels",
            },
        ]
    }
    content: list = []


class _TextOnlyResult:
    structuredContent = None
    content = [_Block("Shared memory is on-chip and fast."), _Block("Use __shared__.")]


class _EmptyResult:
    structuredContent = None
    content: list = []


def test_structured_results_are_mapped():
    docs = _coerce_docs(_StructuredResult(), source="cuda-mcp")
    assert len(docs) == 2
    assert docs[0].title == "Thread Hierarchy"
    assert docs[0].url.endswith("thread-hierarchy")
    assert docs[1].title == "Kernels"
    assert docs[1].snippet.startswith("A kernel")


def test_text_blocks_fallback():
    docs = _coerce_docs(_TextOnlyResult(), source="cuda-mcp")
    assert len(docs) == 2
    assert docs[0].snippet.startswith("Shared memory")


def test_dict_shaped_result():
    docs = _coerce_docs(
        {"structuredContent": {"documents": [{"heading": "Warps", "body": "32 threads"}]}},
        source="cuda-mcp",
    )
    assert docs and docs[0].title == "Warps" and docs[0].snippet == "32 threads"


def test_empty_result_returns_empty_list():
    assert _coerce_docs(_EmptyResult(), source="x") == []


def test_snippet_is_truncated():
    long = "x" * 2000
    docs = _coerce_docs({"content": [{"text": long}]}, source="x")
    assert len(docs[0].snippet) == 800


def test_pick_query_arg_prefers_configured():
    schema = {"properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}}
    assert _pick_query_arg(schema, preferred="query") == "query"


def test_pick_query_arg_finds_synonym():
    schema = {"properties": {"question": {"type": "string"}}}
    assert _pick_query_arg(schema, preferred="query") == "question"


def test_pick_query_arg_first_string_when_no_synonym():
    schema = {"properties": {"foo": {"type": "integer"}, "bar": {"type": "string"}}}
    assert _pick_query_arg(schema, preferred="query") == "bar"


def test_pick_query_arg_fallback_without_schema():
    assert _pick_query_arg(None, preferred="query") == "query"


def test_stub_retriever_returns_nothing():
    import asyncio

    assert asyncio.run(StubRetriever().retrieve("cuda", "threads")) == []


if __name__ == "__main__":
    # Allow running without pytest installed.
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("OK")

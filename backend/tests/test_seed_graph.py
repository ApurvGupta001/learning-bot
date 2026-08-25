"""Tests for the concept-graph validator (pure, no database)."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import pytest
except ImportError:  # allow running standalone without pytest installed
    pytest = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.seed_data import CUDA_CONCEPTS, GraphError, validate_graph  # noqa: E402


def test_real_cuda_graph_is_valid():
    validate_graph(CUDA_CONCEPTS)  # should not raise


def test_detects_duplicate_slugs():
    concepts = [
        {"slug": "a", "prerequisites": []},
        {"slug": "a", "prerequisites": []},
    ]
    with pytest.raises(GraphError):
        validate_graph(concepts)


def test_detects_unknown_prerequisite():
    concepts = [{"slug": "a", "prerequisites": ["ghost"]}]
    with pytest.raises(GraphError):
        validate_graph(concepts)


def test_detects_self_loop():
    concepts = [{"slug": "a", "prerequisites": ["a"]}]
    with pytest.raises(GraphError):
        validate_graph(concepts)


def test_detects_cycle():
    concepts = [
        {"slug": "a", "prerequisites": ["b"]},
        {"slug": "b", "prerequisites": ["a"]},
    ]
    with pytest.raises(GraphError):
        validate_graph(concepts)


def test_accepts_valid_dag():
    concepts = [
        {"slug": "a", "prerequisites": []},
        {"slug": "b", "prerequisites": ["a"]},
        {"slug": "c", "prerequisites": ["a", "b"]},
    ]
    validate_graph(concepts)  # should not raise


if __name__ == "__main__":
    # Run without pytest: emulate raises-checks.
    validate_graph(CUDA_CONCEPTS)
    for bad in (
        [{"slug": "a"}, {"slug": "a"}],
        [{"slug": "a", "prerequisites": ["ghost"]}],
        [{"slug": "a", "prerequisites": ["a"]}],
        [{"slug": "a", "prerequisites": ["b"]}, {"slug": "b", "prerequisites": ["a"]}],
    ):
        try:
            validate_graph(bad)
        except GraphError:
            pass
        else:
            raise SystemExit(f"expected GraphError for {bad}")
    print("OK")

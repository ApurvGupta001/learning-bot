"""The CUDA syllabus as data (source of truth for the seeder).

Concepts reference their prerequisites by **slug** (stable), not database id.
Every prerequisite must appear earlier in this list, which keeps the graph a DAG
(directed acyclic graph) — no cycles. The seeder resolves slugs to ids on insert.
"""

from __future__ import annotations

CUDA_TOPIC = {
    "slug": "cuda",
    "title": "CUDA",
    "description": "NVIDIA's programming model for general-purpose GPU computing.",
}

# order_hint gives a default teaching order; prerequisites drive the real gating.
CUDA_CONCEPTS: list[dict] = [
    {
        "slug": "gpu-vs-cpu",
        "title": "GPU vs CPU execution model",
        "summary": "Why GPUs use many simple cores for massive parallelism, versus a CPU's few powerful cores.",
        "prerequisites": [],
        "order_hint": 1,
    },
    {
        "slug": "threads",
        "title": "Threads",
        "summary": "The smallest unit of execution in CUDA; thousands run the same kernel code in parallel.",
        "prerequisites": ["gpu-vs-cpu"],
        "order_hint": 2,
    },
    {
        "slug": "kernels",
        "title": "Kernels",
        "summary": "GPU functions marked __global__ and launched from the host to run on many threads.",
        "prerequisites": ["threads"],
        "order_hint": 3,
    },
    {
        "slug": "thread-blocks",
        "title": "Thread blocks",
        "summary": "Groups of threads that can cooperate via shared memory and synchronization.",
        "prerequisites": ["threads"],
        "order_hint": 4,
    },
    {
        "slug": "grids",
        "title": "Grids",
        "summary": "A kernel launch creates a grid of thread blocks covering the whole problem.",
        "prerequisites": ["thread-blocks"],
        "order_hint": 5,
    },
    {
        "slug": "thread-indexing",
        "title": "Thread indexing",
        "summary": "Using threadIdx, blockIdx, blockDim, and gridDim to map threads to data elements.",
        "prerequisites": ["kernels", "grids"],
        "order_hint": 6,
    },
    {
        "slug": "memory-hierarchy",
        "title": "Memory hierarchy",
        "summary": "Registers, shared, global, constant, and local memory — and their speed/scope trade-offs.",
        "prerequisites": ["kernels"],
        "order_hint": 7,
    },
    {
        "slug": "global-memory",
        "title": "Global memory",
        "summary": "Large, device-wide memory; coalesced access patterns are key to performance.",
        "prerequisites": ["memory-hierarchy"],
        "order_hint": 8,
    },
    {
        "slug": "shared-memory",
        "title": "Shared memory",
        "summary": "Fast on-chip memory shared within a block (__shared__), ideal for data reuse.",
        "prerequisites": ["memory-hierarchy", "thread-blocks"],
        "order_hint": 9,
    },
    {
        "slug": "synchronization",
        "title": "Thread synchronization",
        "summary": "__syncthreads() coordinates threads in a block so shared-memory use is race-free.",
        "prerequisites": ["shared-memory"],
        "order_hint": 10,
    },
    {
        "slug": "warps",
        "title": "Warps",
        "summary": "Threads execute in groups of 32 (a warp) in lockstep; divergence hurts performance.",
        "prerequisites": ["threads"],
        "order_hint": 11,
    },
    {
        "slug": "occupancy",
        "title": "Occupancy",
        "summary": "How many warps are active per SM; balancing resources to keep the GPU busy.",
        "prerequisites": ["warps", "thread-blocks"],
        "order_hint": 12,
    },
]


class GraphError(ValueError):
    """Raised when the concept graph is malformed."""


def validate_graph(concepts: list[dict]) -> None:
    """Ensure concepts form a valid DAG. Raises GraphError otherwise.

    Pure function (no DB import) so it is trivially unit-testable. Checks:
    unique slugs, prerequisites exist, no self-loops, and acyclicity via a
    topological sort (Kahn's algorithm).
    """
    slugs = [c["slug"] for c in concepts]
    if len(slugs) != len(set(slugs)):
        raise GraphError("duplicate concept slugs found")

    slug_set = set(slugs)
    for c in concepts:
        for p in c.get("prerequisites", []):
            if p == c["slug"]:
                raise GraphError(f"concept '{c['slug']}' lists itself as a prerequisite")
            if p not in slug_set:
                raise GraphError(f"concept '{c['slug']}' has unknown prerequisite '{p}'")

    prereqs = {c["slug"]: set(c.get("prerequisites", [])) for c in concepts}
    resolved: list[str] = [s for s, deps in prereqs.items() if not deps]
    remaining = {s: set(deps) for s, deps in prereqs.items() if deps}
    i = 0
    while i < len(resolved):
        done = resolved[i]
        i += 1
        for s in list(remaining):
            remaining[s].discard(done)
            if not remaining[s]:
                resolved.append(s)
                del remaining[s]
    if remaining:
        raise GraphError(f"cycle detected among concepts: {sorted(remaining)}")

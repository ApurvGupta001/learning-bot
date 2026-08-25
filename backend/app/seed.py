"""Idempotent seeder for the CUDA concept graph.

Run against a live database:
    cd backend && python -m app.seed
    # or in Docker:  docker compose exec backend python -m app.seed

`validate_graph` is a pure function (no DB) so it can be unit-tested: it checks
slugs are unique, prerequisites exist, there are no self-loops, and the graph is
acyclic (a DAG). The seeder is safe to run repeatedly — it upserts by slug.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models import Concept, Topic
from app.seed_data import CUDA_CONCEPTS, CUDA_TOPIC, GraphError, validate_graph

__all__ = ["seed", "validate_graph", "GraphError"]


def _upsert_topic(session: Session, data: dict) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.slug == data["slug"]))
    if topic is None:
        topic = Topic(slug=data["slug"])
        session.add(topic)
    topic.title = data["title"]
    topic.description = data.get("description")
    return topic


def _upsert_concept(session: Session, topic_id: int, data: dict) -> Concept:
    concept = session.scalar(
        select(Concept).where(Concept.topic_id == topic_id, Concept.slug == data["slug"])
    )
    if concept is None:
        concept = Concept(topic_id=topic_id, slug=data["slug"])
        session.add(concept)
    concept.title = data["title"]
    concept.summary = data.get("summary")
    concept.order_hint = data.get("order_hint", 0)
    return concept


def seed(session: Session | None = None) -> dict:
    """Insert/update the CUDA topic + concepts and resolve prerequisites."""
    validate_graph(CUDA_CONCEPTS)

    owns_session = session is None
    session = session or SessionLocal()
    try:
        topic = _upsert_topic(session, CUDA_TOPIC)
        session.flush()  # assigns topic.id

        slug_to_id: dict[str, int] = {}
        for data in CUDA_CONCEPTS:
            concept = _upsert_concept(session, topic.id, data)
            session.flush()  # assigns concept.id
            slug_to_id[data["slug"]] = concept.id

        # Second pass: resolve prerequisite slugs -> ids now that all ids exist.
        for data in CUDA_CONCEPTS:
            concept = session.scalar(
                select(Concept).where(
                    Concept.topic_id == topic.id, Concept.slug == data["slug"]
                )
            )
            concept.prerequisites = [
                slug_to_id[p] for p in data.get("prerequisites", []) if p in slug_to_id
            ]

        session.commit()
        return {"topic": topic.slug, "concepts": len(CUDA_CONCEPTS)}
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    result = seed()
    print(f"Seeded topic '{result['topic']}' with {result['concepts']} concepts.")

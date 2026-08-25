"""Catalog routes: topics and their concept graphs (read-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Concept, Topic
from app.schemas import ConceptOut, TopicOut

router = APIRouter(tags=["catalog"])


@router.get("/topics", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db)) -> list[Topic]:
    return list(db.scalars(select(Topic).order_by(Topic.id)))


@router.get("/topics/{slug}/concepts", response_model=list[ConceptOut])
def list_concepts(slug: str, db: Session = Depends(get_db)) -> list[Concept]:
    topic = db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail=f"topic '{slug}' not found")
    return list(
        db.scalars(
            select(Concept)
            .where(Concept.topic_id == topic.id)
            .order_by(Concept.order_hint, Concept.id)
        )
    )

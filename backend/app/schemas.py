"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    content: str = Field(min_length=1, description="The learner's message.")


class SessionIn(BaseModel):
    user_id: int
    topic: str


class SessionOut(BaseModel):
    id: int
    user_id: int
    topic_id: int


class TopicOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None = None

    model_config = {"from_attributes": True}


class ConceptOut(BaseModel):
    id: int
    slug: str
    title: str
    summary: str | None = None
    prerequisites: list[int] = []
    order_hint: int = 0

    model_config = {"from_attributes": True}

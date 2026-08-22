"""Topic router over the MCP registry table.

Given a topic, return the enabled MCP servers that cover it, highest priority
first. This is what makes "scale with more MCPs based on user preference"
possible: the decision is data (rows), not code.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MCPRegistry


def servers_for_topic(db: Session, topic: str) -> list[MCPRegistry]:
    """Enabled servers whose `topics` array contains `topic`, by priority asc."""
    stmt = (
        select(MCPRegistry)
        .where(MCPRegistry.enabled.is_(True))
        .where(MCPRegistry.topics.any(topic))
        .order_by(MCPRegistry.priority.asc())
    )
    return list(db.scalars(stmt))

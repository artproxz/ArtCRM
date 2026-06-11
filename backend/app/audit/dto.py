from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AuditEvent:
    """Generic audit event boundary."""

    entity_type: str
    entity_id: str
    event_type: str
    actor_ref: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublicationEvent:
    """Catalog publication state transition boundary."""

    entity_type: str
    entity_id: str
    new_status: str
    previous_status: Optional[str] = None
    source_ref: Optional[str] = None


@dataclass(frozen=True)
class MatcherExecutionAuditRef:
    """Reference to a future matcher execution audit record."""

    matcher_execution_id: str
    request_position_ref: Optional[str] = None
    agent_run_ref: Optional[str] = None

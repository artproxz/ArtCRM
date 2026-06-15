from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Optional

from backend.app.auth.permissions import ActorType

from .reasons import AuditEventCategory, AuditEventResult, AuditSeverity


def empty_payload() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class AuditEventRecord:
    """Immutable audit event record produced by the audit service."""

    event_id: str
    timestamp: datetime
    event_name: str
    event_category: AuditEventCategory
    actor_type: ActorType
    actor_id: Optional[str]
    entity_type: Optional[str]
    entity_ref: Optional[str]
    action: Optional[str]
    result: AuditEventResult
    source_module: Optional[str] = None
    correlation_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    request_id: Optional[str] = None
    safe_payload: Mapping[str, Any] = field(default_factory=empty_payload)
    severity: AuditSeverity = AuditSeverity.LOW
    safe_explanation: Optional[str] = None

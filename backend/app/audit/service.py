from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Tuple

from backend.app.auth.permissions import ActorContext

from .dto import AuditEvent, MatcherExecutionAuditRef
from .models import AuditEventRecord
from .reasons import AuditEventCategory, AuditEventResult, AuditSeverity


REDACTED_VALUE = "[REDACTED]"

SENSITIVE_KEY_NAMES = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "client_secret",
        "api_key",
        "authorization",
        "cookie",
        "session",
        "private_key",
        "raw_prompt",
        "full_prompt",
        "raw_llm_prompt",
        "raw_llm_response",
        "email_body",
        "full_email_body",
        "supplier_confidential_response",
        "full_supplier_confidential_response",
    }
)


class AuditService:
    """Append-only in-memory audit event boundary.

    This service records safe audit events only. It does not authorize actions,
    persist to a database, ship logs, call integrations, or implement analytics.
    """

    def __init__(
        self,
        clock: Optional[Callable[[], datetime]] = None,
        event_id_prefix: str = "audit_event",
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._event_id_prefix = event_id_prefix
        self._counter = count(1)
        self._events = []

    def append_event(
        self,
        *,
        actor: ActorContext,
        event_name: str,
        event_category: AuditEventCategory,
        entity_type: Optional[str] = None,
        entity_ref: Optional[str] = None,
        action: Optional[str] = None,
        result: AuditEventResult = AuditEventResult.SUCCESS,
        source_module: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        safe_explanation: Optional[str] = None,
    ) -> AuditEventRecord:
        event = AuditEventRecord(
            event_id=self._next_event_id(),
            timestamp=self._clock(),
            event_name=event_name,
            event_category=self._coerce_category(event_category),
            actor_type=actor.actor_type,
            actor_id=actor.actor_id,
            entity_type=entity_type,
            entity_ref=entity_ref,
            action=action,
            result=self._coerce_result(result),
            source_module=source_module,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            request_id=request_id,
            safe_payload=self.sanitize_payload(payload or {}),
            severity=self._coerce_severity(severity),
            safe_explanation=safe_explanation,
        )
        self._events.append(event)
        return event

    def record_mutation(
        self,
        *,
        actor: ActorContext,
        event_name: str,
        entity_type: str,
        entity_ref: str,
        action: str,
        result: AuditEventResult = AuditEventResult.SUCCESS,
        source_module: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        safe_explanation: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.append_event(
            actor=actor,
            event_name=event_name,
            event_category=AuditEventCategory.MUTATION,
            entity_type=entity_type,
            entity_ref=entity_ref,
            action=action,
            result=result,
            source_module=source_module,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            request_id=request_id,
            payload=payload,
            severity=severity,
            safe_explanation=safe_explanation,
        )

    def record_sensitive_read(
        self,
        *,
        actor: ActorContext,
        event_name: str,
        entity_type: str,
        entity_ref: str,
        action: str = "read",
        result: AuditEventResult = AuditEventResult.SUCCESS,
        source_module: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.HIGH,
        safe_explanation: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.append_event(
            actor=actor,
            event_name=event_name,
            event_category=AuditEventCategory.SENSITIVE_READ,
            entity_type=entity_type,
            entity_ref=entity_ref,
            action=action,
            result=result,
            source_module=source_module,
            correlation_id=correlation_id,
            request_id=request_id,
            payload=payload,
            severity=severity,
            safe_explanation=safe_explanation,
        )

    def list_events(self) -> Tuple[AuditEventRecord, ...]:
        return tuple(self._events)

    def list_by_entity(self, entity_type: str, entity_ref: str) -> Tuple[AuditEventRecord, ...]:
        return tuple(
            event for event in self._events if event.entity_type == entity_type and event.entity_ref == entity_ref
        )

    def list_by_actor(self, actor_id: str) -> Tuple[AuditEventRecord, ...]:
        return tuple(event for event in self._events if event.actor_id == actor_id)

    def list_by_correlation_id(self, correlation_id: str) -> Tuple[AuditEventRecord, ...]:
        return tuple(event for event in self._events if event.correlation_id == correlation_id)

    def list_by_event_name(self, event_name: str) -> Tuple[AuditEventRecord, ...]:
        return tuple(event for event in self._events if event.event_name == event_name)

    def list_by_category(self, event_category: AuditEventCategory) -> Tuple[AuditEventRecord, ...]:
        category = self._coerce_category(event_category)
        return tuple(event for event in self._events if event.event_category == category)

    def record_event(self, event: AuditEvent) -> AuditEvent:
        raise NotImplementedError("Legacy AuditEvent recording is not implemented in ART-CODE-002.")

    def record_matcher_execution(
        self,
        matcher_execution_ref: MatcherExecutionAuditRef,
    ) -> MatcherExecutionAuditRef:
        raise NotImplementedError("Matcher execution audit recording is not implemented in ART-CODE-002.")

    def sanitize_payload(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._deep_freeze(self._sanitize_mapping(payload))

    def _next_event_id(self) -> str:
        return f"{self._event_id_prefix}:{next(self._counter):06d}"

    def _sanitize_mapping(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {str(key): self._sanitize_value(str(key), value) for key, value in payload.items()}

    def _sanitize_value(self, key: str, value: Any) -> Any:
        if self._is_sensitive_key(key):
            return REDACTED_VALUE
        if isinstance(value, Mapping):
            return self._sanitize_mapping(value)
        if isinstance(value, (list, tuple)):
            return [self._sanitize_value("", item) for item in value]
        return value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.strip().lower().replace("-", "_")
        return normalized in SENSITIVE_KEY_NAMES

    def _deep_freeze(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return MappingProxyType({key: self._deep_freeze(inner_value) for key, inner_value in value.items()})
        if isinstance(value, (list, tuple)):
            return tuple(self._deep_freeze(item) for item in value)
        return value

    @staticmethod
    def _coerce_category(event_category: AuditEventCategory) -> AuditEventCategory:
        if isinstance(event_category, AuditEventCategory):
            return event_category
        return AuditEventCategory(event_category)

    @staticmethod
    def _coerce_result(result: AuditEventResult) -> AuditEventResult:
        if isinstance(result, AuditEventResult):
            return result
        return AuditEventResult(result)

    @staticmethod
    def _coerce_severity(severity: AuditSeverity) -> AuditSeverity:
        if isinstance(severity, AuditSeverity):
            return severity
        return AuditSeverity(severity)

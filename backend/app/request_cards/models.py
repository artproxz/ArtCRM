from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Tuple

from .statuses import (
    RequestPositionStatus,
    RequestPriority,
    RequestSourceType,
    RequestStatus,
    coerce_position_status,
    coerce_priority,
    coerce_request_status,
    coerce_source_type,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def empty_position_refs() -> Tuple[str, ...]:
    return ()


@dataclass(frozen=True)
class RequestCard:
    """Request-level foundation entity without API or database coupling."""

    request_id: str
    status: RequestStatus = RequestStatus.DRAFT
    source_type: RequestSourceType = RequestSourceType.UNKNOWN
    source_ref: Optional[str] = None
    counterparty_ref: Optional[str] = None
    customer_ref: Optional[str] = None
    responsible_user_ref: Optional[str] = None
    assistant_user_ref: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    title: Optional[str] = None
    subject: Optional[str] = None
    clean_customer_request: Optional[str] = None
    internal_notes: Optional[str] = None
    priority: RequestPriority = RequestPriority.NORMAL
    position_refs: Tuple[str, ...] = field(default_factory=empty_position_refs)

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", str(self.request_id))
        object.__setattr__(self, "status", coerce_request_status(self.status))
        object.__setattr__(self, "source_type", coerce_source_type(self.source_type))
        object.__setattr__(self, "priority", coerce_priority(self.priority))
        object.__setattr__(self, "position_refs", tuple(str(ref) for ref in self.position_refs))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"request:{self.request_id}"

    def with_status(self, status: RequestStatus, *, updated_at: Optional[datetime] = None) -> "RequestCard":
        return replace(self, status=coerce_request_status(status), updated_at=updated_at or utcnow())

    def with_position_ref(self, position_ref: str, *, updated_at: Optional[datetime] = None) -> "RequestCard":
        position_ref = str(position_ref)
        if position_ref in self.position_refs:
            return self
        return replace(self, position_refs=(*self.position_refs, position_ref), updated_at=updated_at or utcnow())

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "ref": self.ref,
            "status": self.status.value,
            "source_type": self.source_type.value,
            "source_ref": self.source_ref,
            "counterparty_ref": self.counterparty_ref,
            "customer_ref": self.customer_ref,
            "responsible_user_ref": self.responsible_user_ref,
            "assistant_user_ref": self.assistant_user_ref,
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
            "title": self.title,
            "subject": self.subject,
            "clean_customer_request": self.clean_customer_request,
            "internal_notes": self.internal_notes,
            "priority": self.priority.value,
            "position_refs": list(self.position_refs),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "source_type": self.source_type.value,
            "customer_ref": self.customer_ref,
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
            "title": self.title,
            "subject": self.subject,
            "clean_customer_request": self.clean_customer_request,
            "priority": self.priority.value,
            "positions_count": len(self.position_refs),
        }


@dataclass(frozen=True)
class RequestPosition:
    """Line-level foundation entity for product/service request positions."""

    position_id: str
    request_id: str
    line_no: int
    source_text: str
    quantity: Decimal = Decimal("1")
    unit: str = "pcs"
    status: RequestPositionStatus = RequestPositionStatus.NEW
    parsed_intent_ref: Optional[str] = None
    agent_run_ref: Optional[str] = None
    catalog_item_ref: Optional[str] = None
    matcher_run_ref: Optional[str] = None
    needs_review: bool = False
    review_reason: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "position_id", str(self.position_id))
        object.__setattr__(self, "request_id", str(self.request_id))
        object.__setattr__(self, "line_no", int(self.line_no))
        object.__setattr__(self, "source_text", str(self.source_text))
        object.__setattr__(self, "quantity", _coerce_decimal(self.quantity))
        object.__setattr__(self, "unit", str(self.unit))
        object.__setattr__(self, "status", coerce_position_status(self.status))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"request_position:{self.position_id}"

    def with_status(
        self,
        status: RequestPositionStatus,
        *,
        needs_review: Optional[bool] = None,
        review_reason: Optional[str] = None,
        updated_at: Optional[datetime] = None,
    ) -> "RequestPosition":
        next_status = coerce_position_status(status)
        return replace(
            self,
            status=next_status,
            needs_review=next_status == RequestPositionStatus.NEEDS_REVIEW if needs_review is None else needs_review,
            review_reason=review_reason if review_reason is not None else self.review_reason,
            updated_at=updated_at or utcnow(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "ref": self.ref,
            "request_id": self.request_id,
            "request_ref": f"request:{self.request_id}",
            "line_no": self.line_no,
            "source_text": self.source_text,
            "quantity": _decimal_to_json(self.quantity),
            "unit": self.unit,
            "status": self.status.value,
            "parsed_intent_ref": self.parsed_intent_ref,
            "agent_run_ref": self.agent_run_ref,
            "catalog_item_ref": self.catalog_item_ref,
            "matcher_run_ref": self.matcher_run_ref,
            "needs_review": self.needs_review,
            "review_reason": self.review_reason,
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "line_no": self.line_no,
            "source_text": self.source_text,
            "quantity": _decimal_to_json(self.quantity),
            "unit": self.unit,
            "status": self.status.value,
            "needs_review": self.needs_review,
        }


def _coerce_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("datetime value expected")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _datetime_to_json(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_decimal(value: Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _decimal_to_json(value: Decimal) -> int | float | str:
    if value == value.to_integral_value():
        return int(value)
    normalized = value.normalize()
    return str(normalized)

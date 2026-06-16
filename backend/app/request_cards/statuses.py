from __future__ import annotations

from enum import Enum


class RequestStatus(str, Enum):
    """Foundation-level RequestCard statuses."""

    DRAFT = "draft"
    NEW = "new"
    INCOMING = "incoming"
    PARSING = "parsing"
    PARSED = "parsed"
    POSITIONS_EXTRACTED = "positions_extracted"
    IN_REVIEW = "in_review"
    NEEDS_REVIEW = "needs_review"
    READY_FOR_MATCHING = "ready_for_matching"
    MATCHED = "matched"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_SUPPLIER = "waiting_supplier"
    QUOTE_DRAFT = "quote_draft"
    QUOTE_APPROVAL = "quote_approval"
    QUOTE_SENT = "quote_sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CLOSED = "closed"
    CANCELED = "canceled"
    ARCHIVED = "archived"


class RequestPositionStatus(str, Enum):
    """Foundation-level RequestPosition statuses."""

    NEW = "new"
    PARSED = "parsed"
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    READY_FOR_MATCHING = "ready_for_matching"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"
    ARCHIVED = "archived"


class RequestSourceType(str, Enum):
    """Request source families supported by the foundation model."""

    EMAIL = "email"
    MANUAL = "manual"
    CUSTOMER_PORTAL = "customer_portal"
    TENDER = "tender"
    IMPORTED = "imported"
    UNKNOWN = "unknown"


class RequestPriority(str, Enum):
    """Simple priority vocabulary for staff queues."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


def coerce_request_status(status: RequestStatus) -> RequestStatus:
    if isinstance(status, RequestStatus):
        return status
    return RequestStatus(status)


def coerce_position_status(status: RequestPositionStatus) -> RequestPositionStatus:
    if isinstance(status, RequestPositionStatus):
        return status
    return RequestPositionStatus(status)


def coerce_source_type(source_type: RequestSourceType) -> RequestSourceType:
    if isinstance(source_type, RequestSourceType):
        return source_type
    return RequestSourceType(source_type)


def coerce_priority(priority: RequestPriority) -> RequestPriority:
    if isinstance(priority, RequestPriority):
        return priority
    return RequestPriority(priority)

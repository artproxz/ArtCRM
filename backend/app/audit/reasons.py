from __future__ import annotations

from enum import Enum


class AuditEventCategory(str, Enum):
    """Stable audit event categories for backend foundation events."""

    MUTATION = "mutation"
    SENSITIVE_READ = "sensitive_read"
    PERMISSION = "permission"
    STATE_TRANSITION = "state_transition"
    IMPORT = "import"
    AGENT = "agent"
    MATCHER = "matcher"
    SUPPLIER_QUOTE = "supplier_quote"
    QUOTE = "quote"
    DOCUMENT = "document"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    SECURITY = "security"


class AuditEventResult(str, Enum):
    """Stable audit event results."""

    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"
    SKIPPED = "skipped"
    PREVIEWED = "previewed"
    APPLIED = "applied"
    PARTIALLY_APPLIED = "partially_applied"


class AuditSeverity(str, Enum):
    """Risk/severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

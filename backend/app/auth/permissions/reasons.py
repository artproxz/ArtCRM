from __future__ import annotations

from enum import Enum


class PermissionDecisionReason(str, Enum):
    """Stable reason codes for permission decisions."""

    ALLOWED_BY_ROLE_TEMPLATE = "allowed_by_role_template"
    ALLOWED_BY_EXPLICIT_GRANT = "allowed_by_explicit_grant"
    ALLOWED_BY_OWNERSHIP = "allowed_by_ownership"
    ALLOWED_BY_SERVICE_SCOPE = "allowed_by_service_scope"
    DENIED_ANONYMOUS_ACTOR = "denied_anonymous_actor"
    DENIED_UNKNOWN_ACTOR = "denied_unknown_actor"
    DENIED_UNKNOWN_PERMISSION = "denied_unknown_permission"
    DENIED_EXPLICIT_REVOKE = "denied_explicit_revoke"
    DENIED_MISSING_PERMISSION = "denied_missing_permission"
    DENIED_OWNERSHIP_REQUIRED = "denied_ownership_required"
    DENIED_SERVICE_SCOPE = "denied_service_scope"


class FieldMaskingReason(str, Enum):
    """Stable reason codes for field visibility decisions."""

    VISIBLE_PUBLIC_FIELD = "visible_public_field"
    VISIBLE_BY_PERMISSION = "visible_by_permission"
    MASKED_MISSING_PERMISSION = "masked_missing_permission"
    HIDDEN_MISSING_PERMISSION = "hidden_missing_permission"
    DENIED_MISSING_PERMISSION = "denied_missing_permission"
    DENIED_ACTOR = "denied_actor"
    DENIED_UNKNOWN_PERMISSION = "denied_unknown_permission"
    DENIED_EXPLICIT_REVOKE = "denied_explicit_revoke"

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Optional

from .reasons import FieldMaskingReason, PermissionDecisionReason


class ActorType(str, Enum):
    """Backend actor categories used by permission decisions."""

    STAFF_USER = "staff_user"
    CUSTOMER_USER = "customer_user"
    GUEST = "guest"
    SERVICE_ACTOR = "service_actor"
    AGENT = "agent"
    SYSTEM_JOB = "system_job"
    ANONYMOUS = "anonymous"
    UNKNOWN = "unknown"


class FieldVisibility(str, Enum):
    """Visibility decision for a response field."""

    VISIBLE = "visible"
    MASKED = "masked"
    HIDDEN = "hidden"
    DENIED = "denied"


@dataclass(frozen=True)
class ActorContext:
    """Input-only actor context for permission checks.

    This object is intentionally storage-agnostic. Future auth/runtime code can
    build it from real users, service actors, or customer sessions.
    """

    actor_type: ActorType = ActorType.UNKNOWN
    actor_id: Optional[str] = None
    role_template_permissions: FrozenSet[str] = field(default_factory=frozenset)
    explicit_grants: FrozenSet[str] = field(default_factory=frozenset)
    explicit_revokes: FrozenSet[str] = field(default_factory=frozenset)
    owned_object_refs: FrozenSet[str] = field(default_factory=frozenset)
    service_scopes: FrozenSet[str] = field(default_factory=frozenset)
    frontend_visible_permissions: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.actor_type, ActorType):
            object.__setattr__(self, "actor_type", ActorType(self.actor_type))

        for attr in (
            "role_template_permissions",
            "explicit_grants",
            "explicit_revokes",
            "owned_object_refs",
            "service_scopes",
            "frontend_visible_permissions",
        ):
            object.__setattr__(self, attr, frozenset(getattr(self, attr)))


@dataclass(frozen=True)
class PermissionRequest:
    """Permission check request.

    `ownership_required` is generic and does not bind the service to request,
    counterparty, catalog, or any other business entity.
    """

    permission: str
    target_ref: Optional[str] = None
    ownership_required: bool = False
    service_scope: Optional[str] = None
    sensitive: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    """Safe permission decision result."""

    allowed: bool
    reason_code: PermissionDecisionReason
    matched_permission: Optional[str] = None
    masking_required: bool = False
    safe_explanation: Optional[str] = None


@dataclass(frozen=True)
class FieldAccessRequest:
    """Field-level visibility request for future DTO serialization."""

    field_name: str
    required_permission: Optional[str] = None
    target_ref: Optional[str] = None
    ownership_required: bool = False
    service_scope: Optional[str] = None
    missing_permission_visibility: FieldVisibility = FieldVisibility.MASKED


@dataclass(frozen=True)
class FieldMaskingDecision:
    """Safe field visibility decision result."""

    field_name: str
    visibility: FieldVisibility
    reason_code: FieldMaskingReason
    matched_permission: Optional[str] = None
    safe_explanation: Optional[str] = None

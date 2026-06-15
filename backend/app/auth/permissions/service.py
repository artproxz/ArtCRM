from __future__ import annotations

from typing import FrozenSet, Iterable, Optional

from .models import (
    ActorContext,
    ActorType,
    FieldAccessRequest,
    FieldMaskingDecision,
    FieldVisibility,
    PermissionDecision,
    PermissionRequest,
)
from .reasons import FieldMaskingReason, PermissionDecisionReason


SERVICE_ACTOR_TYPES = frozenset({ActorType.SERVICE_ACTOR, ActorType.AGENT, ActorType.SYSTEM_JOB})
USE_REQUEST_PERMISSION = object()


class PermissionDecisionService:
    """Pure permission decision boundary.

    The service has no database, API, session, JWT, UI, audit persistence, or
    business-domain dependency. Callers provide the full actor context as value
    objects and receive safe decision objects.
    """

    def __init__(self, known_permissions: Optional[Iterable[str]] = None) -> None:
        self.known_permissions = frozenset(known_permissions) if known_permissions is not None else None

    def get_effective_permissions(self, actor: ActorContext) -> FrozenSet[str]:
        """Return role template permissions plus grants minus revokes."""

        if actor.actor_type in {ActorType.ANONYMOUS, ActorType.UNKNOWN}:
            return frozenset()

        permissions = (actor.role_template_permissions | actor.explicit_grants) - actor.explicit_revokes
        if self.known_permissions is not None:
            return frozenset(permission for permission in permissions if permission in self.known_permissions)
        return frozenset(permissions)

    def decide(self, actor: ActorContext, request: PermissionRequest) -> PermissionDecision:
        """Decide whether an actor may use a permission for the requested context."""

        if actor.actor_type == ActorType.ANONYMOUS:
            return self._deny(
                PermissionDecisionReason.DENIED_ANONYMOUS_ACTOR,
                request,
                matched_permission=None,
                explanation="Anonymous actors are denied by default.",
            )

        if actor.actor_type == ActorType.UNKNOWN:
            return self._deny(
                PermissionDecisionReason.DENIED_UNKNOWN_ACTOR,
                request,
                matched_permission=None,
                explanation="Unknown actors are denied by default.",
            )

        if self._is_unknown_permission(request.permission):
            return self._deny(
                PermissionDecisionReason.DENIED_UNKNOWN_PERMISSION,
                request,
                matched_permission=None,
                explanation="Requested permission is not registered.",
            )

        if request.permission in actor.explicit_revokes:
            return self._deny(
                PermissionDecisionReason.DENIED_EXPLICIT_REVOKE,
                request,
                explanation="Permission is explicitly revoked.",
            )

        if actor.actor_type in SERVICE_ACTOR_TYPES:
            service_scope_decision = self._decide_service_scope(actor, request)
            if service_scope_decision is not None:
                return service_scope_decision

        if request.ownership_required:
            if not request.target_ref or request.target_ref not in actor.owned_object_refs:
                return self._deny(
                    PermissionDecisionReason.DENIED_OWNERSHIP_REQUIRED,
                    request,
                    explanation="Object ownership is required and was not confirmed.",
                )

            return self._allow(
                PermissionDecisionReason.ALLOWED_BY_OWNERSHIP,
                request.permission,
                "Object ownership scope allows this action.",
            )

        effective_permissions = self.get_effective_permissions(actor)
        if request.permission in effective_permissions:
            if request.permission in actor.explicit_grants and request.permission not in actor.role_template_permissions:
                return self._allow(
                    PermissionDecisionReason.ALLOWED_BY_EXPLICIT_GRANT,
                    request.permission,
                    "Explicit grant allows this action.",
                )

            return self._allow(
                PermissionDecisionReason.ALLOWED_BY_ROLE_TEMPLATE,
                request.permission,
                "Role template allows this action.",
            )

        return self._deny(
            PermissionDecisionReason.DENIED_MISSING_PERMISSION,
            request,
            explanation="Actor does not have the required permission.",
        )

    def decide_field_access(self, actor: ActorContext, request: FieldAccessRequest) -> FieldMaskingDecision:
        """Decide whether a field is visible, masked, hidden, or denied."""

        if request.required_permission is None:
            return FieldMaskingDecision(
                field_name=request.field_name,
                visibility=FieldVisibility.VISIBLE,
                reason_code=FieldMaskingReason.VISIBLE_PUBLIC_FIELD,
                safe_explanation="Field does not require a permission.",
            )

        permission_decision = self.decide(
            actor,
            PermissionRequest(
                permission=request.required_permission,
                target_ref=request.target_ref,
                ownership_required=request.ownership_required,
                service_scope=request.service_scope,
                sensitive=True,
            ),
        )

        if permission_decision.allowed:
            return FieldMaskingDecision(
                field_name=request.field_name,
                visibility=FieldVisibility.VISIBLE,
                reason_code=FieldMaskingReason.VISIBLE_BY_PERMISSION,
                matched_permission=permission_decision.matched_permission,
                safe_explanation="Required permission allows field visibility.",
            )

        return FieldMaskingDecision(
            field_name=request.field_name,
            visibility=request.missing_permission_visibility,
            reason_code=self._field_reason_for_denial(permission_decision, request.missing_permission_visibility),
            matched_permission=permission_decision.matched_permission,
            safe_explanation="Required permission is missing or denied for this field.",
        )

    def _decide_service_scope(self, actor: ActorContext, request: PermissionRequest) -> Optional[PermissionDecision]:
        if not request.service_scope or request.service_scope not in actor.service_scopes:
            return self._deny(
                PermissionDecisionReason.DENIED_SERVICE_SCOPE,
                request,
                explanation="Service actor scope does not allow this action.",
            )

        effective_permissions = self.get_effective_permissions(actor)
        if request.permission in effective_permissions:
            return self._allow(
                PermissionDecisionReason.ALLOWED_BY_SERVICE_SCOPE,
                request.permission,
                "Service actor scope and permission allow this action.",
            )

        return self._deny(
            PermissionDecisionReason.DENIED_MISSING_PERMISSION,
            request,
            explanation="Service actor does not have the required permission.",
        )

    def _is_unknown_permission(self, permission: str) -> bool:
        return self.known_permissions is not None and permission not in self.known_permissions

    @staticmethod
    def _allow(reason_code: PermissionDecisionReason, permission: str, explanation: str) -> PermissionDecision:
        return PermissionDecision(
            allowed=True,
            reason_code=reason_code,
            matched_permission=permission,
            masking_required=False,
            safe_explanation=explanation,
        )

    @staticmethod
    def _deny(
        reason_code: PermissionDecisionReason,
        request: PermissionRequest,
        matched_permission=USE_REQUEST_PERMISSION,
        explanation: str = "Permission denied.",
    ) -> PermissionDecision:
        return PermissionDecision(
            allowed=False,
            reason_code=reason_code,
            matched_permission=request.permission if matched_permission is USE_REQUEST_PERMISSION else matched_permission,
            masking_required=request.sensitive,
            safe_explanation=explanation,
        )

    @staticmethod
    def _field_reason_for_denial(
        permission_decision: PermissionDecision,
        visibility: FieldVisibility,
    ) -> FieldMaskingReason:
        if permission_decision.reason_code in {
            PermissionDecisionReason.DENIED_ANONYMOUS_ACTOR,
            PermissionDecisionReason.DENIED_UNKNOWN_ACTOR,
        }:
            return FieldMaskingReason.DENIED_ACTOR

        if permission_decision.reason_code == PermissionDecisionReason.DENIED_UNKNOWN_PERMISSION:
            return FieldMaskingReason.DENIED_UNKNOWN_PERMISSION

        if permission_decision.reason_code == PermissionDecisionReason.DENIED_EXPLICIT_REVOKE:
            return FieldMaskingReason.DENIED_EXPLICIT_REVOKE

        if visibility == FieldVisibility.HIDDEN:
            return FieldMaskingReason.HIDDEN_MISSING_PERMISSION
        if visibility == FieldVisibility.DENIED:
            return FieldMaskingReason.DENIED_MISSING_PERMISSION
        return FieldMaskingReason.MASKED_MISSING_PERMISSION

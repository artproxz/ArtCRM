from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Mapping, Optional, Tuple

from backend.app.auth.permissions import ActorContext, ActorType
from backend.app.common import ApiError, conflict_error, invalid_state_transition_error, permission_denied_error

from .reasons import TransitionDecisionReason, WorkflowType
from .state_machine import StateMachineDefinition, TransitionRule


def empty_permissions() -> FrozenSet[str]:
    return frozenset()


def empty_provided_fields() -> FrozenSet[str]:
    return frozenset()


@dataclass(frozen=True)
class TransitionRequest:
    """Input-only transition validation request."""

    workflow_type: WorkflowType
    entity_ref: str
    current_state: str
    target_state: str
    expected_state: Optional[str] = None
    actor_context: Optional[ActorContext] = None
    actor_permissions: FrozenSet[str] = field(default_factory=empty_permissions)
    reason: Optional[str] = None
    provided_fields: FrozenSet[str] = field(default_factory=empty_provided_fields)
    correlation_id: Optional[str] = None
    idempotency_key: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "workflow_type", _coerce_workflow_type(self.workflow_type))
        object.__setattr__(self, "entity_ref", str(self.entity_ref))
        object.__setattr__(self, "current_state", str(self.current_state))
        object.__setattr__(self, "target_state", str(self.target_state))
        if self.expected_state is not None:
            object.__setattr__(self, "expected_state", str(self.expected_state))
        object.__setattr__(self, "actor_permissions", frozenset(str(item) for item in self.actor_permissions))
        object.__setattr__(self, "provided_fields", frozenset(str(item) for item in self.provided_fields))


@dataclass(frozen=True)
class TransitionDecision:
    """Safe decision returned by the state transition guard."""

    allowed: bool
    workflow_type: WorkflowType
    entity_ref: str
    from_state: str
    to_state: str
    reason_code: TransitionDecisionReason
    required_permission: Optional[str] = None
    missing_fields: Tuple[str, ...] = ()
    safe_explanation: Optional[str] = None
    error: Optional[ApiError] = None
    correlation_id: Optional[str] = None
    idempotency_key: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "workflow_type", _coerce_workflow_type(self.workflow_type))
        object.__setattr__(self, "reason_code", _coerce_reason(self.reason_code))
        object.__setattr__(self, "missing_fields", tuple(self.missing_fields))


class StateTransitionGuard:
    """Pure state transition decision utility.

    The guard does not mutate entities, persist state, emit audit events, or
    call authorization services. Callers provide the current state and effective
    permission context; the guard returns a safe decision object.
    """

    def __init__(self, state_machines: Iterable[StateMachineDefinition]) -> None:
        self._state_machines: Mapping[WorkflowType, StateMachineDefinition] = {
            definition.workflow_type: definition for definition in state_machines
        }

    def decide(self, request: TransitionRequest) -> TransitionDecision:
        definition = self._state_machines.get(request.workflow_type)
        if definition is None:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_UNKNOWN_WORKFLOW,
                safe_explanation="Workflow is not registered.",
            )

        if request.current_state not in definition.known_states:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_UNKNOWN_STATE,
                safe_explanation="Current state is not registered for this workflow.",
            )

        if request.target_state not in definition.known_states:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_UNKNOWN_STATE,
                safe_explanation="Target state is not registered for this workflow.",
            )

        if request.expected_state is not None and request.expected_state != request.current_state:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_EXPECTED_STATE_MISMATCH,
                error=conflict_error(
                    entity_ref=request.entity_ref,
                    details={
                        "reason_code": TransitionDecisionReason.DENIED_EXPECTED_STATE_MISMATCH.value,
                        "expected_state": request.expected_state,
                        "current_state": request.current_state,
                    },
                ),
                safe_explanation="Expected state does not match current state.",
            )

        rule = definition.find_rule(request.current_state, request.target_state)

        if request.current_state == request.target_state and (rule is None or not rule.allow_self_transition):
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_SELF_TRANSITION,
                safe_explanation="Self-transition is not allowed.",
            )

        if request.current_state in definition.terminal_states and rule is None:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_TERMINAL_STATE,
                safe_explanation="Current state is terminal.",
            )

        if rule is None:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION,
                safe_explanation="Transition rule is not registered.",
            )

        actor_type = self._actor_type(request)
        if actor_type in rule.forbidden_actor_types:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_ACTOR_TYPE,
                rule=rule,
                safe_explanation="Actor type is forbidden for this transition.",
            )

        if rule.allowed_actor_types and actor_type not in rule.allowed_actor_types:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_ACTOR_TYPE,
                rule=rule,
                safe_explanation="Actor type is not allowed for this transition.",
            )

        if rule.required_permission and rule.required_permission not in self._effective_permissions(request):
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_MISSING_PERMISSION,
                rule=rule,
                error=permission_denied_error(
                    permission=rule.required_permission,
                    entity_ref=request.entity_ref,
                    details={"reason_code": TransitionDecisionReason.DENIED_MISSING_PERMISSION.value},
                ),
                safe_explanation="Required permission is missing.",
            )

        if rule.requires_reason and not self._has_reason(request.reason):
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_MISSING_REASON,
                rule=rule,
                safe_explanation="A safe reason is required for this transition.",
            )

        missing_fields = tuple(sorted(rule.required_fields - request.provided_fields))
        if missing_fields:
            return self._deny(
                request,
                TransitionDecisionReason.DENIED_MISSING_REQUIRED_FIELDS,
                rule=rule,
                missing_fields=missing_fields,
                safe_explanation="Required fields are missing.",
            )

        return TransitionDecision(
            allowed=True,
            workflow_type=request.workflow_type,
            entity_ref=request.entity_ref,
            from_state=request.current_state,
            to_state=request.target_state,
            reason_code=TransitionDecisionReason.ALLOWED_TRANSITION,
            required_permission=rule.required_permission,
            safe_explanation=rule.description or "Transition is allowed.",
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
        )

    def _deny(
        self,
        request: TransitionRequest,
        reason_code: TransitionDecisionReason,
        *,
        rule: Optional[TransitionRule] = None,
        missing_fields: Tuple[str, ...] = (),
        error: Optional[ApiError] = None,
        safe_explanation: Optional[str] = None,
    ) -> TransitionDecision:
        if error is None:
            error = invalid_state_transition_error(
                entity_ref=request.entity_ref,
                from_state=request.current_state,
                to_state=request.target_state,
                details={
                    "reason_code": reason_code.value,
                    "missing_fields": missing_fields,
                },
            )

        return TransitionDecision(
            allowed=False,
            workflow_type=request.workflow_type,
            entity_ref=request.entity_ref,
            from_state=request.current_state,
            to_state=request.target_state,
            reason_code=reason_code,
            required_permission=rule.required_permission if rule else None,
            missing_fields=missing_fields,
            safe_explanation=safe_explanation,
            error=error,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
        )

    def _effective_permissions(self, request: TransitionRequest) -> FrozenSet[str]:
        permissions = set(request.actor_permissions)
        actor = request.actor_context
        if actor is not None:
            permissions.update(actor.role_template_permissions)
            permissions.update(actor.explicit_grants)
            permissions.difference_update(actor.explicit_revokes)
        return frozenset(permissions)

    @staticmethod
    def _actor_type(request: TransitionRequest) -> ActorType:
        if request.actor_context is None:
            return ActorType.UNKNOWN
        return request.actor_context.actor_type

    @staticmethod
    def _has_reason(reason: Optional[str]) -> bool:
        return reason is not None and bool(str(reason).strip())


def _coerce_workflow_type(workflow_type: WorkflowType) -> WorkflowType:
    if isinstance(workflow_type, WorkflowType):
        return workflow_type
    try:
        return WorkflowType(workflow_type)
    except ValueError:
        return WorkflowType.GENERIC


def _coerce_reason(reason: TransitionDecisionReason) -> TransitionDecisionReason:
    if isinstance(reason, TransitionDecisionReason):
        return reason
    return TransitionDecisionReason(reason)

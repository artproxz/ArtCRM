from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Tuple

from backend.app.auth.permissions import ActorType

from .reasons import WorkflowType


def empty_string_set() -> FrozenSet[str]:
    return frozenset()


def empty_actor_type_set() -> FrozenSet[ActorType]:
    return frozenset()


def empty_transition_rules() -> Tuple["TransitionRule", ...]:
    return ()


@dataclass(frozen=True)
class TransitionRule:
    """Declarative rule for one allowed state transition."""

    from_state: str
    to_state: str
    required_permission: Optional[str] = None
    requires_reason: bool = False
    required_fields: FrozenSet[str] = field(default_factory=empty_string_set)
    allowed_actor_types: FrozenSet[ActorType] = field(default_factory=empty_actor_type_set)
    forbidden_actor_types: FrozenSet[ActorType] = field(default_factory=empty_actor_type_set)
    allow_self_transition: bool = False
    description: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "from_state", str(self.from_state))
        object.__setattr__(self, "to_state", str(self.to_state))
        object.__setattr__(self, "required_fields", frozenset(str(field) for field in self.required_fields))
        object.__setattr__(
            self,
            "allowed_actor_types",
            frozenset(_coerce_actor_type(actor_type) for actor_type in self.allowed_actor_types),
        )
        object.__setattr__(
            self,
            "forbidden_actor_types",
            frozenset(_coerce_actor_type(actor_type) for actor_type in self.forbidden_actor_types),
        )


@dataclass(frozen=True)
class StateMachineDefinition:
    """Storage-agnostic state machine definition."""

    workflow_type: WorkflowType
    known_states: FrozenSet[str]
    transition_rules: Tuple[TransitionRule, ...] = field(default_factory=empty_transition_rules)
    terminal_states: FrozenSet[str] = field(default_factory=empty_string_set)
    initial_state: Optional[str] = None

    def __post_init__(self) -> None:
        workflow_type = _coerce_workflow_type(self.workflow_type)
        known_states = frozenset(str(state) for state in self.known_states)
        transition_rules = tuple(self.transition_rules)
        terminal_states = frozenset(str(state) for state in self.terminal_states)
        initial_state = None if self.initial_state is None else str(self.initial_state)

        object.__setattr__(self, "workflow_type", workflow_type)
        object.__setattr__(self, "known_states", known_states)
        object.__setattr__(self, "transition_rules", transition_rules)
        object.__setattr__(self, "terminal_states", terminal_states)
        object.__setattr__(self, "initial_state", initial_state)

    def find_rule(self, from_state: str, to_state: str) -> Optional[TransitionRule]:
        for rule in self.transition_rules:
            if rule.from_state == from_state and rule.to_state == to_state:
                return rule
        return None


def _coerce_actor_type(actor_type: ActorType) -> ActorType:
    if isinstance(actor_type, ActorType):
        return actor_type
    try:
        return ActorType(actor_type)
    except ValueError:
        return ActorType.UNKNOWN


def _coerce_workflow_type(workflow_type: WorkflowType) -> WorkflowType:
    if isinstance(workflow_type, WorkflowType):
        return workflow_type
    try:
        return WorkflowType(workflow_type)
    except ValueError:
        return WorkflowType.GENERIC

"""Workflow/state transition guard foundation for ArtCRM backend."""

from .guard import StateTransitionGuard, TransitionDecision, TransitionRequest
from .reasons import TransitionDecisionReason, WorkflowType
from .state_machine import StateMachineDefinition, TransitionRule

__all__ = [
    "StateMachineDefinition",
    "StateTransitionGuard",
    "TransitionDecision",
    "TransitionDecisionReason",
    "TransitionRequest",
    "TransitionRule",
    "WorkflowType",
]

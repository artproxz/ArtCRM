from __future__ import annotations

from backend.app.workflow import StateMachineDefinition, TransitionRule, WorkflowType

from .statuses import RequestPositionStatus, RequestStatus


def request_state_machine() -> StateMachineDefinition:
    return StateMachineDefinition(
        workflow_type=WorkflowType.REQUEST,
        known_states=frozenset(status.value for status in RequestStatus),
        terminal_states=frozenset(
            {
                RequestStatus.CLOSED.value,
                RequestStatus.CANCELED.value,
                RequestStatus.REJECTED.value,
                RequestStatus.ARCHIVED.value,
            }
        ),
        initial_state=RequestStatus.DRAFT.value,
        transition_rules=(
            TransitionRule(RequestStatus.INCOMING.value, RequestStatus.PARSED.value, required_permission="agent.run"),
            TransitionRule(RequestStatus.PARSED.value, RequestStatus.DRAFT.value, required_permission="request.create"),
            TransitionRule(RequestStatus.DRAFT.value, RequestStatus.NEW.value, required_permission="request.change_status"),
            TransitionRule(RequestStatus.NEW.value, RequestStatus.PARSING.value, required_permission="agent.run"),
            TransitionRule(RequestStatus.PARSING.value, RequestStatus.POSITIONS_EXTRACTED.value, required_permission="agent.run"),
            TransitionRule(
                RequestStatus.POSITIONS_EXTRACTED.value,
                RequestStatus.IN_REVIEW.value,
                required_permission="request.edit",
            ),
            TransitionRule(RequestStatus.DRAFT.value, RequestStatus.NEEDS_REVIEW.value, required_permission="request.edit"),
            TransitionRule(RequestStatus.NEEDS_REVIEW.value, RequestStatus.DRAFT.value, required_permission="request.edit"),
            TransitionRule(
                RequestStatus.DRAFT.value,
                RequestStatus.READY_FOR_MATCHING.value,
                required_permission="request.change_status",
            ),
            TransitionRule(
                RequestStatus.IN_REVIEW.value,
                RequestStatus.READY_FOR_MATCHING.value,
                required_permission="request.change_status",
            ),
            TransitionRule(
                RequestStatus.READY_FOR_MATCHING.value,
                RequestStatus.MATCHED.value,
                required_permission="matcher.run",
            ),
            TransitionRule(
                RequestStatus.MATCHED.value,
                RequestStatus.WAITING_SUPPLIER.value,
                required_permission="supplier_quote.create_request",
            ),
            TransitionRule(
                RequestStatus.MATCHED.value,
                RequestStatus.QUOTE_DRAFT.value,
                required_permission="quote.create_draft",
            ),
            TransitionRule(
                RequestStatus.IN_REVIEW.value,
                RequestStatus.WAITING_CUSTOMER.value,
                required_permission="request.change_status",
            ),
            TransitionRule(
                RequestStatus.IN_REVIEW.value,
                RequestStatus.WAITING_SUPPLIER.value,
                required_permission="supplier_quote.create_request",
            ),
            TransitionRule(
                RequestStatus.IN_REVIEW.value,
                RequestStatus.QUOTE_DRAFT.value,
                required_permission="quote.create_draft",
            ),
            TransitionRule(
                RequestStatus.QUOTE_DRAFT.value,
                RequestStatus.QUOTE_APPROVAL.value,
                required_permission="quote.request_approval",
            ),
            TransitionRule(
                RequestStatus.QUOTE_APPROVAL.value,
                RequestStatus.QUOTE_SENT.value,
                required_permission="quote.send",
            ),
            TransitionRule(
                RequestStatus.QUOTE_DRAFT.value,
                RequestStatus.QUOTE_SENT.value,
                required_permission="quote.send",
            ),
            TransitionRule(
                RequestStatus.QUOTE_SENT.value,
                RequestStatus.WAITING_CUSTOMER.value,
                required_permission="request.change_status",
            ),
            TransitionRule(
                RequestStatus.WAITING_CUSTOMER.value,
                RequestStatus.ACCEPTED.value,
                required_permission="request.change_status",
            ),
            TransitionRule(
                RequestStatus.ACCEPTED.value,
                RequestStatus.CLOSED.value,
                required_permission="request.change_status",
            ),
            *_cancel_rules(),
            TransitionRule(RequestStatus.CLOSED.value, RequestStatus.ARCHIVED.value, required_permission="request.archive"),
            TransitionRule(RequestStatus.CANCELED.value, RequestStatus.ARCHIVED.value, required_permission="request.archive"),
            TransitionRule(RequestStatus.REJECTED.value, RequestStatus.ARCHIVED.value, required_permission="request.archive"),
        ),
    )


def request_position_state_machine() -> StateMachineDefinition:
    return StateMachineDefinition(
        workflow_type=WorkflowType.REQUEST_POSITION,
        known_states=frozenset(status.value for status in RequestPositionStatus),
        terminal_states=frozenset(
            {
                RequestPositionStatus.APPROVED.value,
                RequestPositionStatus.REJECTED.value,
                RequestPositionStatus.CANCELED.value,
                RequestPositionStatus.ARCHIVED.value,
            }
        ),
        initial_state=RequestPositionStatus.NEW.value,
        transition_rules=(
            TransitionRule(
                RequestPositionStatus.NEW.value,
                RequestPositionStatus.PARSED.value,
                required_permission="agent.run",
            ),
            TransitionRule(
                RequestPositionStatus.PARSED.value,
                RequestPositionStatus.DRAFT.value,
                required_permission="request_position.create",
            ),
            TransitionRule(
                RequestPositionStatus.DRAFT.value,
                RequestPositionStatus.NEEDS_REVIEW.value,
                required_permission="request_position.edit",
            ),
            TransitionRule(
                RequestPositionStatus.NEEDS_REVIEW.value,
                RequestPositionStatus.DRAFT.value,
                required_permission="request_position.edit",
            ),
            TransitionRule(
                RequestPositionStatus.DRAFT.value,
                RequestPositionStatus.READY_FOR_MATCHING.value,
                required_permission="request_position.edit",
            ),
            TransitionRule(
                RequestPositionStatus.READY_FOR_MATCHING.value,
                RequestPositionStatus.MATCHED.value,
                required_permission="matcher.run",
            ),
            TransitionRule(
                RequestPositionStatus.MATCHED.value,
                RequestPositionStatus.APPROVED.value,
                required_permission="request_position.approve",
            ),
            *_position_reject_or_cancel_rules(),
            TransitionRule(
                RequestPositionStatus.REJECTED.value,
                RequestPositionStatus.ARCHIVED.value,
                required_permission="request_position.edit",
            ),
            TransitionRule(
                RequestPositionStatus.CANCELED.value,
                RequestPositionStatus.ARCHIVED.value,
                required_permission="request_position.edit",
            ),
        ),
    )


def _cancel_rules() -> tuple[TransitionRule, ...]:
    return tuple(
        TransitionRule(status.value, RequestStatus.CANCELED.value, required_permission="request.change_status", requires_reason=True)
        for status in RequestStatus
        if status
        not in {
            RequestStatus.CLOSED,
            RequestStatus.CANCELED,
            RequestStatus.REJECTED,
            RequestStatus.ARCHIVED,
        }
    ) + tuple(
        TransitionRule(status.value, RequestStatus.REJECTED.value, required_permission="request.change_status", requires_reason=True)
        for status in RequestStatus
        if status
        not in {
            RequestStatus.CLOSED,
            RequestStatus.CANCELED,
            RequestStatus.REJECTED,
            RequestStatus.ARCHIVED,
        }
    )


def _position_reject_or_cancel_rules() -> tuple[TransitionRule, ...]:
    active_statuses = {
        RequestPositionStatus.NEW,
        RequestPositionStatus.PARSED,
        RequestPositionStatus.DRAFT,
        RequestPositionStatus.NEEDS_REVIEW,
        RequestPositionStatus.READY_FOR_MATCHING,
        RequestPositionStatus.MATCHED,
    }
    return tuple(
        TransitionRule(status.value, RequestPositionStatus.REJECTED.value, required_permission="request_position.edit", requires_reason=True)
        for status in active_statuses
    ) + tuple(
        TransitionRule(status.value, RequestPositionStatus.CANCELED.value, required_permission="request_position.edit", requires_reason=True)
        for status in active_statuses
    )

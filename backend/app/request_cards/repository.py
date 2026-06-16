from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Generic, Iterable, Optional, TypeVar

from backend.app.auth.permissions import ActorContext
from backend.app.common import ApiError, conflict_error, invalid_state_transition_error, not_found_error
from backend.app.workflow import StateTransitionGuard, TransitionDecision, TransitionRequest

from .models import RequestCard, RequestPosition
from .state_machines import request_position_state_machine, request_state_machine
from .statuses import RequestPositionStatus, RequestStatus, coerce_position_status, coerce_request_status


T = TypeVar("T")


@dataclass(frozen=True)
class RepositoryResult(Generic[T]):
    """Small safe result object for repository/test-store operations."""

    success: bool
    value: Optional[T] = None
    error: Optional[ApiError] = None
    transition_decision: Optional[TransitionDecision] = None

    @property
    def is_error(self) -> bool:
        return not self.success


class InMemoryRequestRepository:
    """Deterministic in-memory RequestCard/RequestPosition store.

    This is a test/foundation repository only. It does not connect to a
    production database, emit audit events, or perform authorization runtime
    checks outside of the supplied StateTransitionGuard inputs.
    """

    def __init__(self, guard: Optional[StateTransitionGuard] = None) -> None:
        self._guard = guard or StateTransitionGuard([request_state_machine(), request_position_state_machine()])
        self._requests: dict[str, RequestCard] = {}
        self._positions: dict[str, RequestPosition] = {}

    def create_request(self, request: RequestCard) -> RepositoryResult[RequestCard]:
        if request.request_id in self._requests:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=request.ref, details={"reason": "request_id_already_exists"}),
            )
        self._requests[request.request_id] = request
        return RepositoryResult(success=True, value=request)

    def get_request(self, request_id: str) -> RepositoryResult[RequestCard]:
        request = self._requests.get(str(request_id))
        if request is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"request:{request_id}", details={"entity": "RequestCard"}),
            )
        return RepositoryResult(success=True, value=request)

    def list_requests(self) -> tuple[RequestCard, ...]:
        return tuple(sorted(self._requests.values(), key=lambda request: request.created_at))

    def update_request(self, request: RequestCard) -> RepositoryResult[RequestCard]:
        existing = self._requests.get(request.request_id)
        if existing is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=request.ref, details={"entity": "RequestCard"}),
            )
        if request.status != existing.status:
            return RepositoryResult(
                success=False,
                error=invalid_state_transition_error(
                    entity_ref=request.ref,
                    from_state=existing.status.value,
                    to_state=request.status.value,
                    details={"reason": "direct_status_update_forbidden"},
                ),
            )
        self._requests[request.request_id] = request
        return RepositoryResult(success=True, value=request)

    def update_request_status(
        self,
        request_id: str,
        target_status: RequestStatus,
        *,
        expected_state: Optional[RequestStatus] = None,
        actor_context: Optional[ActorContext] = None,
        actor_permissions: Optional[Iterable[str]] = None,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> RepositoryResult[RequestCard]:
        existing = self.get_request(request_id)
        if not existing.success:
            return existing

        request = existing.value
        assert request is not None
        target_status = coerce_request_status(target_status)
        decision = self._guard.decide(
            TransitionRequest(
                workflow_type=request_state_machine().workflow_type,
                entity_ref=request.ref,
                current_state=request.status.value,
                target_state=target_status.value,
                expected_state=_status_value(expected_state),
                actor_context=actor_context,
                actor_permissions=_freeze_permissions(actor_permissions),
                reason=reason,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        )
        if not decision.allowed:
            return RepositoryResult(success=False, error=decision.error, transition_decision=decision)

        updated = request.with_status(target_status)
        self._requests[request.request_id] = updated
        return RepositoryResult(success=True, value=updated, transition_decision=decision)

    def add_position(self, position: RequestPosition) -> RepositoryResult[RequestPosition]:
        request_result = self.get_request(position.request_id)
        if not request_result.success:
            return RepositoryResult(success=False, error=request_result.error)
        if position.position_id in self._positions:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=position.ref, details={"reason": "position_id_already_exists"}),
            )

        request = request_result.value
        assert request is not None
        self._positions[position.position_id] = position
        self._requests[request.request_id] = request.with_position_ref(position.ref)
        return RepositoryResult(success=True, value=position)

    def list_positions_by_request(self, request_id: str) -> RepositoryResult[tuple[RequestPosition, ...]]:
        request_result = self.get_request(request_id)
        if not request_result.success:
            return RepositoryResult(success=False, error=request_result.error)

        positions = tuple(
            sorted(
                (position for position in self._positions.values() if position.request_id == str(request_id)),
                key=lambda position: position.line_no,
            )
        )
        return RepositoryResult(success=True, value=positions)

    def get_position(self, position_id: str) -> RepositoryResult[RequestPosition]:
        position = self._positions.get(str(position_id))
        if position is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"request_position:{position_id}", details={"entity": "RequestPosition"}),
            )
        return RepositoryResult(success=True, value=position)

    def update_position(self, position: RequestPosition) -> RepositoryResult[RequestPosition]:
        existing = self._positions.get(position.position_id)
        if existing is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=position.ref, details={"entity": "RequestPosition"}),
            )
        if position.request_id not in self._requests:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"request:{position.request_id}", details={"entity": "RequestCard"}),
            )
        if position.status != existing.status:
            return RepositoryResult(
                success=False,
                error=invalid_state_transition_error(
                    entity_ref=position.ref,
                    from_state=existing.status.value,
                    to_state=position.status.value,
                    details={"reason": "direct_status_update_forbidden"},
                ),
            )

        self._positions[position.position_id] = position
        return RepositoryResult(success=True, value=position)

    def update_position_status(
        self,
        position_id: str,
        target_status: RequestPositionStatus,
        *,
        expected_state: Optional[RequestPositionStatus] = None,
        actor_context: Optional[ActorContext] = None,
        actor_permissions: Optional[Iterable[str]] = None,
        reason: Optional[str] = None,
        review_reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> RepositoryResult[RequestPosition]:
        existing = self.get_position(position_id)
        if not existing.success:
            return existing

        position = existing.value
        assert position is not None
        target_status = coerce_position_status(target_status)
        decision = self._guard.decide(
            TransitionRequest(
                workflow_type=request_position_state_machine().workflow_type,
                entity_ref=position.ref,
                current_state=position.status.value,
                target_state=target_status.value,
                expected_state=_position_status_value(expected_state),
                actor_context=actor_context,
                actor_permissions=_freeze_permissions(actor_permissions),
                reason=reason,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        )
        if not decision.allowed:
            return RepositoryResult(success=False, error=decision.error, transition_decision=decision)

        updated = position.with_status(target_status, review_reason=review_reason)
        self._positions[position.position_id] = updated
        return RepositoryResult(success=True, value=updated, transition_decision=decision)


def _status_value(status: Optional[RequestStatus]) -> Optional[str]:
    if status is None:
        return None
    return coerce_request_status(status).value


def _position_status_value(status: Optional[RequestPositionStatus]) -> Optional[str]:
    if status is None:
        return None
    return coerce_position_status(status).value


def _freeze_permissions(permissions: Optional[Iterable[str]]) -> FrozenSet[str]:
    if permissions is None:
        return frozenset()
    return frozenset(str(permission) for permission in permissions)

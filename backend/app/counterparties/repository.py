from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from backend.app.common import ApiError, conflict_error, invalid_state_transition_error, not_found_error

from .models import Counterparty, CounterpartyContact
from .normalization import build_contact_dedup_key, build_counterparty_dedup_key
from .statuses import CounterpartyStatus


T = TypeVar("T")


@dataclass(frozen=True)
class RepositoryResult(Generic[T]):
    """Small safe result object for counterparty repository operations."""

    success: bool
    value: Optional[T] = None
    error: Optional[ApiError] = None

    @property
    def is_error(self) -> bool:
        return not self.success


class InMemoryCounterpartyRepository:
    """Deterministic in-memory counterparty registry store for tests/foundation."""

    def __init__(self) -> None:
        self._counterparties: dict[str, Counterparty] = {}
        self._contacts: dict[str, CounterpartyContact] = {}

    def create_counterparty(self, counterparty: Counterparty) -> RepositoryResult[Counterparty]:
        if counterparty.counterparty_id in self._counterparties:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=counterparty.ref, details={"reason": "counterparty_id_already_exists"}),
            )
        self._counterparties[counterparty.counterparty_id] = counterparty
        return RepositoryResult(success=True, value=counterparty)

    def get_counterparty(self, counterparty_id: str) -> RepositoryResult[Counterparty]:
        counterparty = self._counterparties.get(str(counterparty_id))
        if counterparty is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"counterparty:{counterparty_id}", details={"entity": "Counterparty"}),
            )
        return RepositoryResult(success=True, value=counterparty)

    def list_counterparties(self) -> tuple[Counterparty, ...]:
        return tuple(sorted(self._counterparties.values(), key=lambda counterparty: counterparty.created_at))

    def update_counterparty(self, counterparty: Counterparty) -> RepositoryResult[Counterparty]:
        existing = self._counterparties.get(counterparty.counterparty_id)
        if existing is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=counterparty.ref, details={"entity": "Counterparty"}),
            )
        if counterparty.status != existing.status:
            return RepositoryResult(
                success=False,
                error=invalid_state_transition_error(
                    entity_ref=counterparty.ref,
                    from_state=existing.status.value,
                    to_state=counterparty.status.value,
                    details={"reason": "direct_status_update_forbidden"},
                ),
            )
        if counterparty.contact_refs != existing.contact_refs:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=counterparty.ref, details={"reason": "direct_contact_refs_update_forbidden"}),
            )
        self._counterparties[counterparty.counterparty_id] = counterparty
        return RepositoryResult(success=True, value=counterparty)

    def archive_counterparty(self, counterparty_id: str) -> RepositoryResult[Counterparty]:
        existing = self.get_counterparty(counterparty_id)
        if not existing.success:
            return existing
        counterparty = existing.value
        assert counterparty is not None
        archived = counterparty.with_status(CounterpartyStatus.ARCHIVED)
        self._counterparties[counterparty.counterparty_id] = archived
        return RepositoryResult(success=True, value=archived)

    def create_contact(self, contact: CounterpartyContact) -> RepositoryResult[CounterpartyContact]:
        counterparty_result = self.get_counterparty(contact.counterparty_id)
        if not counterparty_result.success:
            return RepositoryResult(success=False, error=counterparty_result.error)
        if contact.contact_id in self._contacts:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=contact.ref, details={"reason": "contact_id_already_exists"}),
            )

        counterparty = counterparty_result.value
        assert counterparty is not None
        self._contacts[contact.contact_id] = contact
        self._counterparties[counterparty.counterparty_id] = counterparty.with_contact_ref(contact.ref)
        if contact.is_primary:
            self.set_primary_contact(contact.counterparty_id, contact.contact_id)
            return RepositoryResult(success=True, value=self._contacts[contact.contact_id])
        return RepositoryResult(success=True, value=contact)

    def get_contact(self, contact_id: str) -> RepositoryResult[CounterpartyContact]:
        contact = self._contacts.get(str(contact_id))
        if contact is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"counterparty_contact:{contact_id}", details={"entity": "CounterpartyContact"}),
            )
        return RepositoryResult(success=True, value=contact)

    def list_contacts_by_counterparty(self, counterparty_id: str) -> RepositoryResult[tuple[CounterpartyContact, ...]]:
        counterparty_result = self.get_counterparty(counterparty_id)
        if not counterparty_result.success:
            return RepositoryResult(success=False, error=counterparty_result.error)
        contacts = tuple(
            sorted(
                (contact for contact in self._contacts.values() if contact.counterparty_id == str(counterparty_id)),
                key=lambda contact: contact.created_at,
            )
        )
        return RepositoryResult(success=True, value=contacts)

    def update_contact(self, contact: CounterpartyContact) -> RepositoryResult[CounterpartyContact]:
        existing = self._contacts.get(contact.contact_id)
        if existing is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=contact.ref, details={"entity": "CounterpartyContact"}),
            )
        if contact.counterparty_id not in self._counterparties:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"counterparty:{contact.counterparty_id}", details={"entity": "Counterparty"}),
            )
        if contact.counterparty_id != existing.counterparty_id:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=contact.ref, details={"reason": "counterparty_id_change_forbidden"}),
            )
        if contact.is_primary != existing.is_primary:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=contact.ref, details={"reason": "direct_primary_update_forbidden"}),
            )
        self._contacts[contact.contact_id] = contact
        return RepositoryResult(success=True, value=contact)

    def set_primary_contact(self, counterparty_id: str, contact_id: str) -> RepositoryResult[CounterpartyContact]:
        counterparty_result = self.get_counterparty(counterparty_id)
        if not counterparty_result.success:
            return RepositoryResult(success=False, error=counterparty_result.error)

        selected = self._contacts.get(str(contact_id))
        if selected is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"counterparty_contact:{contact_id}", details={"entity": "CounterpartyContact"}),
            )
        if selected.counterparty_id != str(counterparty_id):
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=selected.ref, details={"reason": "contact_belongs_to_other_counterparty"}),
            )

        for current in tuple(self._contacts.values()):
            if current.counterparty_id == str(counterparty_id):
                self._contacts[current.contact_id] = current.with_primary(current.contact_id == str(contact_id))
        return RepositoryResult(success=True, value=self._contacts[str(contact_id)])

    def find_counterparty_by_dedup_key(self, key: str) -> RepositoryResult[Counterparty]:
        for counterparty in self._counterparties.values():
            if build_counterparty_dedup_key(counterparty) == key:
                return RepositoryResult(success=True, value=counterparty)
        return RepositoryResult(success=False, error=not_found_error(entity_ref=key, details={"entity": "Counterparty"}))

    def find_contact_by_dedup_key(self, key: str) -> RepositoryResult[CounterpartyContact]:
        for contact in self._contacts.values():
            if build_contact_dedup_key(contact) == key:
                return RepositoryResult(success=True, value=contact)
        return RepositoryResult(success=False, error=not_found_error(entity_ref=key, details={"entity": "CounterpartyContact"}))

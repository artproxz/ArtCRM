"""Counterparty registry backend foundation models."""

from .models import Counterparty, CounterpartyContact
from .normalization import (
    build_contact_dedup_key,
    build_counterparty_dedup_key,
    merge_unique_values,
    normalize_email,
    normalize_inn,
    normalize_kpp,
    normalize_name,
    normalize_ogrn,
    normalize_phone,
    normalize_tag,
    normalize_website,
)
from .repository import InMemoryCounterpartyRepository, RepositoryResult
from .statuses import CounterpartySourceType, CounterpartyStatus, CounterpartyType

__all__ = [
    "Counterparty",
    "CounterpartyContact",
    "CounterpartySourceType",
    "CounterpartyStatus",
    "CounterpartyType",
    "InMemoryCounterpartyRepository",
    "RepositoryResult",
    "build_contact_dedup_key",
    "build_counterparty_dedup_key",
    "merge_unique_values",
    "normalize_email",
    "normalize_inn",
    "normalize_kpp",
    "normalize_name",
    "normalize_ogrn",
    "normalize_phone",
    "normalize_tag",
    "normalize_website",
]

from __future__ import annotations

from enum import Enum


class CounterpartyStatus(str, Enum):
    """Foundation-level counterparty lifecycle statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    MERGED = "merged"
    BLOCKED = "blocked"


class CounterpartyType(str, Enum):
    """Counterparty type vocabulary for normalized registry records."""

    COMPANY = "company"
    INDIVIDUAL_ENTREPRENEUR = "individual_entrepreneur"
    PERSON = "person"
    UNKNOWN = "unknown"


class CounterpartySourceType(str, Enum):
    """Source labels for future creation/import workflows."""

    AMOCRM = "amocrm"
    MANUAL = "manual"
    EMAIL = "email"
    CUSTOMER_PORTAL = "customer_portal"
    IMPORTED = "imported"
    UNKNOWN = "unknown"


def coerce_counterparty_status(status: CounterpartyStatus) -> CounterpartyStatus:
    if isinstance(status, CounterpartyStatus):
        return status
    return CounterpartyStatus(status)


def coerce_counterparty_type(counterparty_type: CounterpartyType) -> CounterpartyType:
    if isinstance(counterparty_type, CounterpartyType):
        return counterparty_type
    return CounterpartyType(counterparty_type)


def coerce_source_type(source_type: CounterpartySourceType) -> CounterpartySourceType:
    if isinstance(source_type, CounterpartySourceType):
        return source_type
    return CounterpartySourceType(source_type)

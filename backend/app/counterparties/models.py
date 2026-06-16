from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .normalization import (
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
from .statuses import (
    CounterpartySourceType,
    CounterpartyStatus,
    CounterpartyType,
    coerce_counterparty_status,
    coerce_counterparty_type,
    coerce_source_type,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def empty_tuple() -> Tuple[str, ...]:
    return ()


def empty_external_refs() -> Mapping[str, str]:
    return MappingProxyType({})


@dataclass(frozen=True)
class Counterparty:
    """Canonical counterparty registry value object.

    Future amoCRM CSV aliases must map into these canonical fields instead of
    creating duplicate backend fields for source column variants.
    """

    counterparty_id: str
    display_name: str
    legal_name: Optional[str] = None
    status: CounterpartyStatus = CounterpartyStatus.ACTIVE
    counterparty_type: CounterpartyType = CounterpartyType.COMPANY
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    normalized_display_name: Optional[str] = None
    normalized_legal_name: Optional[str] = None
    primary_email: Optional[str] = None
    emails: Tuple[str, ...] = field(default_factory=empty_tuple)
    primary_phone: Optional[str] = None
    phones: Tuple[str, ...] = field(default_factory=empty_tuple)
    primary_website: Optional[str] = None
    websites: Tuple[str, ...] = field(default_factory=empty_tuple)
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[CounterpartySourceType] = None
    category: Optional[str] = None
    customer_level: Optional[str] = None
    annual_turnover: Optional[str] = None
    responsible_user_ref: Optional[str] = None
    external_refs: Mapping[str, str] = field(default_factory=empty_external_refs)
    tags: Tuple[str, ...] = field(default_factory=empty_tuple)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    contact_refs: Tuple[str, ...] = field(default_factory=empty_tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "counterparty_id", str(self.counterparty_id))
        object.__setattr__(self, "display_name", str(self.display_name).strip())
        object.__setattr__(self, "status", coerce_counterparty_status(self.status))
        object.__setattr__(self, "counterparty_type", coerce_counterparty_type(self.counterparty_type))
        object.__setattr__(self, "inn", normalize_inn(self.inn))
        object.__setattr__(self, "kpp", normalize_kpp(self.kpp))
        object.__setattr__(self, "ogrn", normalize_ogrn(self.ogrn))
        object.__setattr__(
            self,
            "normalized_display_name",
            normalize_name(self.normalized_display_name) or normalize_name(self.display_name),
        )
        object.__setattr__(
            self,
            "normalized_legal_name",
            normalize_name(self.normalized_legal_name) or normalize_name(self.legal_name),
        )
        primary_email = normalize_email(self.primary_email)
        primary_phone = normalize_phone(self.primary_phone)
        primary_website = normalize_website(self.primary_website)
        object.__setattr__(self, "primary_email", primary_email)
        object.__setattr__(self, "primary_phone", primary_phone)
        object.__setattr__(self, "primary_website", primary_website)
        object.__setattr__(self, "emails", merge_unique_values(primary_email, (normalize_email(value) for value in self.emails)))
        object.__setattr__(self, "phones", merge_unique_values(primary_phone, (normalize_phone(value) for value in self.phones)))
        object.__setattr__(
            self,
            "websites",
            merge_unique_values(primary_website, (normalize_website(value) for value in self.websites)),
        )
        object.__setattr__(self, "source", None if self.source is None else coerce_source_type(self.source))
        object.__setattr__(self, "external_refs", _freeze_string_mapping(self.external_refs))
        object.__setattr__(self, "tags", tuple(value for value in (normalize_tag(tag) for tag in self.tags) if value))
        object.__setattr__(self, "contact_refs", tuple(str(ref) for ref in self.contact_refs))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"counterparty:{self.counterparty_id}"

    def with_status(self, status: CounterpartyStatus, *, updated_at: Optional[datetime] = None) -> "Counterparty":
        return replace(self, status=coerce_counterparty_status(status), updated_at=updated_at or utcnow())

    def with_contact_ref(self, contact_ref: str, *, updated_at: Optional[datetime] = None) -> "Counterparty":
        contact_ref = str(contact_ref)
        if contact_ref in self.contact_refs:
            return self
        return replace(self, contact_refs=(*self.contact_refs, contact_ref), updated_at=updated_at or utcnow())

    def to_dict(self) -> dict[str, Any]:
        return {
            "counterparty_id": self.counterparty_id,
            "ref": self.ref,
            "display_name": self.display_name,
            "legal_name": self.legal_name,
            "status": self.status.value,
            "counterparty_type": self.counterparty_type.value,
            "inn": self.inn,
            "kpp": self.kpp,
            "ogrn": self.ogrn,
            "normalized_display_name": self.normalized_display_name,
            "normalized_legal_name": self.normalized_legal_name,
            "primary_email": self.primary_email,
            "emails": list(self.emails),
            "primary_phone": self.primary_phone,
            "phones": list(self.phones),
            "primary_website": self.primary_website,
            "websites": list(self.websites),
            "legal_address": self.legal_address,
            "actual_address": self.actual_address,
            "industry": self.industry,
            "source": self.source.value if self.source else None,
            "category": self.category,
            "customer_level": self.customer_level,
            "annual_turnover": self.annual_turnover,
            "responsible_user_ref": self.responsible_user_ref,
            "external_refs": dict(self.external_refs),
            "tags": list(self.tags),
            "notes": self.notes,
            "internal_notes": self.internal_notes,
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
            "contact_refs": list(self.contact_refs),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "counterparty_id": self.counterparty_id,
            "display_name": self.display_name,
            "legal_name": self.legal_name,
            "status": self.status.value,
            "counterparty_type": self.counterparty_type.value,
            "inn": self.inn,
            "primary_email": self.primary_email,
            "primary_phone": self.primary_phone,
            "primary_website": self.primary_website,
            "industry": self.industry,
            "category": self.category,
            "customer_level": self.customer_level,
        }


@dataclass(frozen=True)
class CounterpartyContact:
    """First-class contact person linked to one Counterparty."""

    contact_id: str
    counterparty_id: str
    full_name: str
    position_title: Optional[str] = None
    primary_email: Optional[str] = None
    emails: Tuple[str, ...] = field(default_factory=empty_tuple)
    primary_phone: Optional[str] = None
    phones: Tuple[str, ...] = field(default_factory=empty_tuple)
    is_primary: bool = False
    source: Optional[CounterpartySourceType] = None
    external_refs: Mapping[str, str] = field(default_factory=empty_external_refs)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "contact_id", str(self.contact_id))
        object.__setattr__(self, "counterparty_id", str(self.counterparty_id))
        object.__setattr__(self, "full_name", str(self.full_name).strip())
        primary_email = normalize_email(self.primary_email)
        primary_phone = normalize_phone(self.primary_phone)
        object.__setattr__(self, "primary_email", primary_email)
        object.__setattr__(self, "primary_phone", primary_phone)
        object.__setattr__(self, "emails", merge_unique_values(primary_email, (normalize_email(value) for value in self.emails)))
        object.__setattr__(self, "phones", merge_unique_values(primary_phone, (normalize_phone(value) for value in self.phones)))
        object.__setattr__(self, "is_primary", bool(self.is_primary))
        object.__setattr__(self, "source", None if self.source is None else coerce_source_type(self.source))
        object.__setattr__(self, "external_refs", _freeze_string_mapping(self.external_refs))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"counterparty_contact:{self.contact_id}"

    def with_primary(self, is_primary: bool, *, updated_at: Optional[datetime] = None) -> "CounterpartyContact":
        return replace(self, is_primary=bool(is_primary), updated_at=updated_at or utcnow())

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "ref": self.ref,
            "counterparty_id": self.counterparty_id,
            "counterparty_ref": f"counterparty:{self.counterparty_id}",
            "full_name": self.full_name,
            "position_title": self.position_title,
            "primary_email": self.primary_email,
            "emails": list(self.emails),
            "primary_phone": self.primary_phone,
            "phones": list(self.phones),
            "is_primary": self.is_primary,
            "source": self.source.value if self.source else None,
            "external_refs": dict(self.external_refs),
            "notes": self.notes,
            "internal_notes": self.internal_notes,
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "counterparty_id": self.counterparty_id,
            "full_name": self.full_name,
            "position_title": self.position_title,
            "primary_email": self.primary_email,
            "primary_phone": self.primary_phone,
            "is_primary": self.is_primary,
        }


def _freeze_string_mapping(mapping: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(
        {
            str(key): str(value)
            for key, value in dict(mapping or {}).items()
            if str(key).strip() and str(value).strip()
        }
    )


def _coerce_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("datetime value expected")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _datetime_to_json(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

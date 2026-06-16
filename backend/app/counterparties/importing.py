from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from io import StringIO
from typing import Any, Mapping, Optional

from .models import Counterparty, CounterpartyContact
from .normalization import (
    build_contact_dedup_key,
    build_counterparty_dedup_key,
    merge_unique_values,
    normalize_name,
    normalize_tag,
)
from .repository import InMemoryCounterpartyRepository
from .statuses import CounterpartySourceType


ROW_STATUS_CREATE = "create"
ROW_STATUS_UPDATE = "update"
ROW_STATUS_DUPLICATE = "duplicate"
ROW_STATUS_SKIPPED = "skipped"
ROW_STATUS_ERROR = "error"


COMPANY_NAME_ALIASES = ("Название компании",)
LEGAL_NAME_ALIASES = ("Полное юридическое наименование",)
INN_ALIASES = ("ИНН компании",)
KPP_ALIASES = ("КПП",)
OGRN_ALIASES = ("ОГРН",)
RESPONSIBLE_ALIASES = ("Ответственный",)
REQUEST_TYPE_ALIASES = ("Тип заявки",)
CATEGORY_ALIASES = ("Категория",)
INDUSTRY_ALIASES = ("Сфера деятельности", "Сфера")
ANNUAL_TURNOVER_ALIASES = ("ОБОРОТ за год",)
SOURCE_ALIASES = ("Источник",)
CUSTOMER_LEVEL_ALIASES = ("Уровень клиента",)
PHONE_ALIASES = ("Телефон компании", "Дополнительный телефон")
EMAIL_ALIASES = ("Email компании", "Официальная почта")
WEBSITE_ALIASES = ("Cайт компании", "Сайт компании", "Сайт", "Web2")
ACTUAL_ADDRESS_ALIASES = ("Фактический адрес компании",)
LEGAL_ADDRESS_ALIASES = ("Юридический адрес компании",)
NOTES_ALIASES = ("Примечание",)
AMOCRM_ID_ALIASES = ("amoCRM ID",)
TAGS_ALIASES = ("Теги amoCRM",)
AMOCRM_DEALS_ALIASES = ("Сделки amoCRM",)
CONTRACT_ALIASES = ("ДОГОВОР / УСЛ.-Я",)
AMOCRM_CREATED_AT_ALIASES = ("Дата создания amoCRM",)
CONTACT_NAME_ALIASES = ("Контактное лицо",)
CONTACT_POSITION_ALIASES = ("Должность",)
CONTACT_EMAIL_ALIASES = ("Почта контактного лица",)
CONTACT_PHONE_ALIASES = ("Телефон контактного лица",)


@dataclass(frozen=True)
class CounterpartyCsvImportSummary:
    rows_total: int = 0
    counterparties_created: int = 0
    counterparties_updated: int = 0
    counterparties_skipped: int = 0
    contacts_created: int = 0
    contacts_updated: int = 0
    contacts_skipped: int = 0
    duplicates: int = 0
    errors: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "rows_total": self.rows_total,
            "counterparties_created": self.counterparties_created,
            "counterparties_updated": self.counterparties_updated,
            "counterparties_skipped": self.counterparties_skipped,
            "contacts_created": self.contacts_created,
            "contacts_updated": self.contacts_updated,
            "contacts_skipped": self.contacts_skipped,
            "duplicates": self.duplicates,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class CounterpartyCsvImportRowResult:
    row_number: int
    status: str
    counterparty_dedup_key: Optional[str] = None
    contact_dedup_key: Optional[str] = None
    counterparty_preview: Optional[Mapping[str, Any]] = None
    contact_preview: Optional[Mapping[str, Any]] = None
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "status": self.status,
            "counterparty_dedup_key": self.counterparty_dedup_key,
            "contact_dedup_key": self.contact_dedup_key,
            "counterparty_preview": dict(self.counterparty_preview) if self.counterparty_preview else None,
            "contact_preview": dict(self.contact_preview) if self.contact_preview else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class CounterpartyCsvImportPreview:
    summary: CounterpartyCsvImportSummary
    rows: tuple[CounterpartyCsvImportRowResult, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "rows": [row.to_dict() for row in self.rows],
        }


@dataclass(frozen=True)
class CounterpartyCsvApplyResult:
    summary: CounterpartyCsvImportSummary
    rows: tuple[CounterpartyCsvImportRowResult, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "rows": [row.to_dict() for row in self.rows],
        }


@dataclass(frozen=True)
class CounterpartyCsvMappedRow:
    row_number: int
    counterparty: Optional[Counterparty] = None
    contact: Optional[CounterpartyContact] = None
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return self.counterparty is not None and not self.errors


def parse_counterparty_csv_text(csv_text: str) -> tuple[dict[str, str], ...]:
    if not csv_text or not csv_text.strip():
        return ()

    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        return ()

    rows: list[dict[str, str]] = []
    for row in reader:
        normalized_row: dict[str, str] = {}
        for key, value in row.items():
            if key is None:
                continue
            normalized_row[_normalize_header(key)] = "" if value is None else str(value).strip()
        rows.append(normalized_row)
    return tuple(rows)


def map_counterparty_csv_row(row: Mapping[str, str], row_number: int) -> CounterpartyCsvMappedRow:
    display_name = _first_value(row, COMPANY_NAME_ALIASES)
    legal_name = _first_value(row, LEGAL_NAME_ALIASES)
    inn = _first_value(row, INN_ALIASES)

    if not display_name and not inn:
        return CounterpartyCsvMappedRow(
            row_number=row_number,
            errors=("missing_company_identity",),
            warnings=("row_has_no_company_name_or_inn",),
        )

    counterparty_id = _counterparty_id_for_row(row_number)
    external_refs = _external_refs(row)
    notes = _notes(row)
    source = _source_from_value(_first_value(row, SOURCE_ALIASES))
    phones = _values(row, PHONE_ALIASES)
    emails = _values(row, EMAIL_ALIASES)
    websites = _values(row, WEBSITE_ALIASES)
    tags = _tags(row)
    counterparty = Counterparty(
        counterparty_id=counterparty_id,
        display_name=display_name or legal_name or f"Imported counterparty {row_number}",
        legal_name=legal_name,
        inn=inn,
        kpp=_first_value(row, KPP_ALIASES),
        ogrn=_first_value(row, OGRN_ALIASES),
        primary_phone=phones[0] if phones else None,
        phones=tuple(phones[1:]),
        primary_email=emails[0] if emails else None,
        emails=tuple(emails[1:]),
        primary_website=websites[0] if websites else None,
        websites=tuple(websites[1:]),
        actual_address=_first_value(row, ACTUAL_ADDRESS_ALIASES),
        legal_address=_first_value(row, LEGAL_ADDRESS_ALIASES),
        industry=_first_value(row, INDUSTRY_ALIASES),
        source=source,
        category=_first_value(row, CATEGORY_ALIASES),
        customer_level=_first_value(row, CUSTOMER_LEVEL_ALIASES),
        annual_turnover=_first_value(row, ANNUAL_TURNOVER_ALIASES),
        responsible_user_ref=_responsible_ref(_first_value(row, RESPONSIBLE_ALIASES)),
        external_refs=external_refs,
        tags=tags,
        notes=notes,
    )
    contact = _contact_from_row(row, row_number, counterparty.counterparty_id)
    return CounterpartyCsvMappedRow(row_number=row_number, counterparty=counterparty, contact=contact)


def preview_counterparty_csv_import(
    csv_text: str,
    repository: InMemoryCounterpartyRepository,
) -> CounterpartyCsvImportPreview:
    rows = parse_counterparty_csv_text(csv_text)
    results: list[CounterpartyCsvImportRowResult] = []
    seen_counterparty_keys: set[str] = set()
    seen_contact_keys: set[str] = set()

    for index, row in enumerate(rows, start=2):
        mapped = map_counterparty_csv_row(row, index)
        if not mapped.is_valid:
            results.append(
                CounterpartyCsvImportRowResult(
                    row_number=index,
                    status=ROW_STATUS_SKIPPED,
                    errors=mapped.errors,
                    warnings=mapped.warnings,
                )
            )
            continue

        assert mapped.counterparty is not None
        counterparty_key = build_counterparty_dedup_key(mapped.counterparty)
        existing_counterparty = _find_counterparty(repository, counterparty_key)
        status = ROW_STATUS_CREATE
        warnings = list(mapped.warnings)
        if existing_counterparty is not None:
            status = ROW_STATUS_UPDATE
        elif counterparty_key in seen_counterparty_keys:
            status = ROW_STATUS_DUPLICATE
            warnings.append("counterparty_duplicate_in_import")
        seen_counterparty_keys.add(counterparty_key)

        contact = _contact_for_counterparty(mapped.contact, existing_counterparty or mapped.counterparty)
        contact_key = build_contact_dedup_key(contact) if contact else None
        if contact_key:
            if _find_contact(repository, contact_key) is not None or contact_key in seen_contact_keys:
                warnings.append("contact_duplicate")
            seen_contact_keys.add(contact_key)

        results.append(
            CounterpartyCsvImportRowResult(
                row_number=index,
                status=status,
                counterparty_dedup_key=counterparty_key,
                contact_dedup_key=contact_key,
                counterparty_preview=mapped.counterparty.to_dict(),
                contact_preview=contact.to_dict() if contact else None,
                warnings=tuple(warnings),
            )
        )

    return CounterpartyCsvImportPreview(summary=_preview_summary(results), rows=tuple(results))


def apply_counterparty_csv_import(
    csv_text: str,
    repository: InMemoryCounterpartyRepository,
) -> CounterpartyCsvApplyResult:
    rows = parse_counterparty_csv_text(csv_text)
    results: list[CounterpartyCsvImportRowResult] = []
    counts = {
        "counterparties_created": 0,
        "counterparties_updated": 0,
        "counterparties_skipped": 0,
        "contacts_created": 0,
        "contacts_updated": 0,
        "contacts_skipped": 0,
        "duplicates": 0,
        "errors": 0,
    }

    for index, row in enumerate(rows, start=2):
        mapped = map_counterparty_csv_row(row, index)
        if not mapped.is_valid:
            counts["counterparties_skipped"] += 1
            if mapped.errors:
                counts["errors"] += 1
            results.append(
                CounterpartyCsvImportRowResult(
                    row_number=index,
                    status=ROW_STATUS_SKIPPED,
                    errors=mapped.errors,
                    warnings=mapped.warnings,
                )
            )
            continue

        assert mapped.counterparty is not None
        counterparty_key = build_counterparty_dedup_key(mapped.counterparty)
        existing_counterparty = _find_counterparty(repository, counterparty_key)
        row_errors: list[str] = []
        row_warnings: list[str] = []

        if existing_counterparty is None:
            candidate = replace(
                mapped.counterparty,
                counterparty_id=_unique_counterparty_id(repository, mapped.counterparty.counterparty_id),
            )
            created = repository.create_counterparty(candidate)
            if not created.success or created.value is None:
                counts["counterparties_skipped"] += 1
                counts["errors"] += 1
                row_errors.append("counterparty_create_failed")
                results.append(
                    CounterpartyCsvImportRowResult(
                        row_number=index,
                        status=ROW_STATUS_ERROR,
                        counterparty_dedup_key=counterparty_key,
                        errors=tuple(row_errors),
                    )
                )
                continue
            counterparty = created.value
            status = ROW_STATUS_CREATE
            counts["counterparties_created"] += 1
        else:
            counterparty = _merge_counterparty(existing_counterparty, mapped.counterparty)
            updated = repository.update_counterparty(counterparty)
            if not updated.success or updated.value is None:
                counts["counterparties_skipped"] += 1
                counts["errors"] += 1
                row_errors.append("counterparty_update_failed")
                results.append(
                    CounterpartyCsvImportRowResult(
                        row_number=index,
                        status=ROW_STATUS_ERROR,
                        counterparty_dedup_key=counterparty_key,
                        errors=tuple(row_errors),
                    )
                )
                continue
            counterparty = updated.value
            status = ROW_STATUS_UPDATE
            counts["counterparties_updated"] += 1
            counts["duplicates"] += 1
            row_warnings.append("counterparty_dedup_matched")

        contact = _contact_for_counterparty(mapped.contact, counterparty)
        contact_key = build_contact_dedup_key(contact) if contact else None
        if contact is None:
            counts["contacts_skipped"] += 1
        else:
            existing_contact = _find_contact(repository, contact_key)
            if existing_contact is None:
                contact = replace(contact, contact_id=_unique_contact_id(repository, contact.contact_id))
                created_contact = repository.create_contact(contact)
                if created_contact.success and created_contact.value is not None:
                    contact = created_contact.value
                    counts["contacts_created"] += 1
                else:
                    counts["contacts_skipped"] += 1
                    counts["errors"] += 1
                    row_errors.append("contact_create_failed")
            else:
                contact = _merge_contact(existing_contact, contact)
                updated_contact = repository.update_contact(contact)
                if updated_contact.success and updated_contact.value is not None:
                    contact = updated_contact.value
                    counts["contacts_updated"] += 1
                    counts["duplicates"] += 1
                    row_warnings.append("contact_dedup_matched")
                else:
                    counts["contacts_skipped"] += 1
                    counts["errors"] += 1
                    row_errors.append("contact_update_failed")

        results.append(
            CounterpartyCsvImportRowResult(
                row_number=index,
                status=ROW_STATUS_ERROR if row_errors else status,
                counterparty_dedup_key=counterparty_key,
                contact_dedup_key=contact_key,
                counterparty_preview=counterparty.to_dict(),
                contact_preview=contact.to_dict() if contact else None,
                errors=tuple(row_errors),
                warnings=tuple(row_warnings),
            )
        )

    summary = CounterpartyCsvImportSummary(rows_total=len(rows), **counts)
    return CounterpartyCsvApplyResult(summary=summary, rows=tuple(results))


def _preview_summary(rows: list[CounterpartyCsvImportRowResult]) -> CounterpartyCsvImportSummary:
    counterparties_created = 0
    counterparties_updated = 0
    counterparties_skipped = 0
    contacts_created = 0
    contacts_updated = 0
    contacts_skipped = 0
    duplicates = 0
    errors = 0
    for row in rows:
        if row.status == ROW_STATUS_CREATE:
            counterparties_created += 1
        if row.status == ROW_STATUS_UPDATE:
            counterparties_updated += 1
            duplicates += 1
        if row.status == ROW_STATUS_DUPLICATE:
            duplicates += 1
        if row.status in {ROW_STATUS_SKIPPED, ROW_STATUS_ERROR}:
            counterparties_skipped += 1
        if row.errors:
            errors += 1
        if row.contact_preview is None:
            contacts_skipped += 1
        elif "contact_duplicate" in row.warnings:
            contacts_updated += 1
            duplicates += 1
        else:
            contacts_created += 1
    return CounterpartyCsvImportSummary(
        rows_total=len(rows),
        counterparties_created=counterparties_created,
        counterparties_updated=counterparties_updated,
        counterparties_skipped=counterparties_skipped,
        contacts_created=contacts_created,
        contacts_updated=contacts_updated,
        contacts_skipped=contacts_skipped,
        duplicates=duplicates,
        errors=errors,
    )


def _contact_from_row(row: Mapping[str, str], row_number: int, counterparty_id: str) -> Optional[CounterpartyContact]:
    full_name = _first_value(row, CONTACT_NAME_ALIASES)
    emails = _values(row, CONTACT_EMAIL_ALIASES)
    phones = _values(row, CONTACT_PHONE_ALIASES)
    if not full_name and not emails and not phones:
        return None

    return CounterpartyContact(
        contact_id=_contact_id_for_row(row_number),
        counterparty_id=counterparty_id,
        full_name=full_name or (emails[0] if emails else phones[0]),
        position_title=_first_value(row, CONTACT_POSITION_ALIASES),
        primary_email=emails[0] if emails else None,
        emails=tuple(emails[1:]),
        primary_phone=phones[0] if phones else None,
        phones=tuple(phones[1:]),
        source=CounterpartySourceType.AMOCRM,
    )


def _contact_for_counterparty(
    contact: Optional[CounterpartyContact],
    counterparty: Counterparty,
) -> Optional[CounterpartyContact]:
    if contact is None:
        return None
    return replace(contact, counterparty_id=counterparty.counterparty_id)


def _find_counterparty(repository: InMemoryCounterpartyRepository, dedup_key: str) -> Optional[Counterparty]:
    result = repository.find_counterparty_by_dedup_key(dedup_key)
    return result.value if result.success else None


def _find_contact(repository: InMemoryCounterpartyRepository, dedup_key: Optional[str]) -> Optional[CounterpartyContact]:
    if not dedup_key:
        return None
    result = repository.find_contact_by_dedup_key(dedup_key)
    return result.value if result.success else None


def _merge_counterparty(existing: Counterparty, incoming: Counterparty) -> Counterparty:
    return replace(
        incoming,
        counterparty_id=existing.counterparty_id,
        status=existing.status,
        contact_refs=existing.contact_refs,
        created_at=existing.created_at,
        external_refs={**dict(existing.external_refs), **dict(incoming.external_refs)},
        tags=tuple(merge_unique_values(None, (*existing.tags, *incoming.tags))),
    )


def _merge_contact(existing: CounterpartyContact, incoming: CounterpartyContact) -> CounterpartyContact:
    return replace(
        incoming,
        contact_id=existing.contact_id,
        counterparty_id=existing.counterparty_id,
        is_primary=existing.is_primary,
        created_at=existing.created_at,
        external_refs={**dict(existing.external_refs), **dict(incoming.external_refs)},
    )


def _normalize_header(header: str) -> str:
    return str(header).replace("\ufeff", "").strip()


def _row_get(row: Mapping[str, str], alias: str) -> str:
    return str(row.get(_normalize_header(alias), "") or "").strip()


def _first_value(row: Mapping[str, str], aliases: tuple[str, ...]) -> Optional[str]:
    for alias in aliases:
        value = _row_get(row, alias)
        if value:
            return value
    return None


def _values(row: Mapping[str, str], aliases: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for alias in aliases:
        value = _row_get(row, alias)
        if value:
            values.append(value)
    return values


def _tags(row: Mapping[str, str]) -> tuple[str, ...]:
    tags: list[str] = []
    for value in _values(row, TAGS_ALIASES):
        tags.extend(_split_multi_value(value))
    return tuple(tag for tag in (normalize_tag(tag) for tag in tags) if tag)


def _notes(row: Mapping[str, str]) -> Optional[str]:
    parts: list[str] = []
    note = _first_value(row, NOTES_ALIASES)
    if note:
        parts.append(note)
    metadata_aliases = (
        ("request_type", REQUEST_TYPE_ALIASES),
        ("amocrm_deals", AMOCRM_DEALS_ALIASES),
        ("contract_terms", CONTRACT_ALIASES),
    )
    for label, aliases in metadata_aliases:
        value = _first_value(row, aliases)
        if value:
            parts.append(f"{label}: {value}")
    source_value = _first_value(row, SOURCE_ALIASES)
    if source_value and _source_from_value(source_value) is None:
        parts.append(f"source: {source_value}")
    return "\n".join(parts) if parts else None


def _external_refs(row: Mapping[str, str]) -> dict[str, str]:
    refs: dict[str, str] = {}
    amocrm_id = _first_value(row, AMOCRM_ID_ALIASES)
    if amocrm_id:
        refs["amocrm_id"] = amocrm_id
    amocrm_created_at = _first_value(row, AMOCRM_CREATED_AT_ALIASES)
    if amocrm_created_at:
        refs["amocrm_created_at"] = amocrm_created_at
    return refs


def _source_from_value(value: Optional[str]) -> Optional[CounterpartySourceType]:
    if not value:
        return None
    normalized = normalize_name(value)
    source_map = {
        "amocrm": CounterpartySourceType.AMOCRM,
        "amo crm": CounterpartySourceType.AMOCRM,
        "manual": CounterpartySourceType.MANUAL,
        "email": CounterpartySourceType.EMAIL,
        "mail": CounterpartySourceType.EMAIL,
        "customer_portal": CounterpartySourceType.CUSTOMER_PORTAL,
        "customer portal": CounterpartySourceType.CUSTOMER_PORTAL,
        "imported": CounterpartySourceType.IMPORTED,
    }
    return source_map.get(normalized or "")


def _responsible_ref(value: Optional[str]) -> Optional[str]:
    normalized = normalize_name(value)
    if not normalized:
        return None
    return f"imported_responsible:{normalized.replace(' ', '-')}"


def _split_multi_value(value: str) -> list[str]:
    normalized = value.replace("\n", ";").replace(",", ";")
    return [item.strip() for item in normalized.split(";") if item.strip()]


def _counterparty_id_for_row(row_number: int) -> str:
    return f"imported-cp-{row_number - 1:06d}"


def _contact_id_for_row(row_number: int) -> str:
    return f"imported-contact-{row_number - 1:06d}"


def _unique_counterparty_id(repository: InMemoryCounterpartyRepository, candidate: str) -> str:
    return _unique_id(lambda value: repository.get_counterparty(value).success, candidate)


def _unique_contact_id(repository: InMemoryCounterpartyRepository, candidate: str) -> str:
    return _unique_id(lambda value: repository.get_contact(value).success, candidate)


def _unique_id(exists, candidate: str) -> str:
    if not exists(candidate):
        return candidate
    index = 2
    while exists(f"{candidate}-{index}"):
        index += 1
    return f"{candidate}-{index}"

from __future__ import annotations

import re
from typing import Iterable, Optional
from urllib.parse import urlparse


def normalize_inn(value: Optional[str]) -> Optional[str]:
    return _digits_or_none(value)


def normalize_kpp(value: Optional[str]) -> Optional[str]:
    return _digits_or_none(value)


def normalize_ogrn(value: Optional[str]) -> Optional[str]:
    return _digits_or_none(value)


def normalize_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def normalize_phone(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    digits = "".join(character for character in raw if character.isdigit())
    if not digits:
        return None
    return f"+{digits}" if raw.startswith("+") else digits


def normalize_website(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    parse_target = raw if "://" in raw else f"//{raw}"
    parsed = urlparse(parse_target)
    host = (parsed.netloc or parsed.path).strip().lower()
    path = parsed.path if parsed.netloc else ""
    if not host:
        return None

    normalized = host.rstrip("/")
    if path and parsed.netloc:
        normalized = f"{normalized}/{path.strip('/')}"
    return normalized.rstrip("/") or None


def normalize_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value).strip().lower())
    return normalized or None


def normalize_tag(value: Optional[str]) -> Optional[str]:
    return normalize_name(value)


def merge_unique_values(primary: Optional[str], values: Iterable[Optional[str]]) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in (primary, *tuple(values)):
        if value is None:
            continue
        normalized = str(value).strip()
        if not normalized:
            continue
        dedup_key = normalized.lower()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        merged.append(normalized)
    return tuple(merged)


def build_counterparty_dedup_key(counterparty: object) -> str:
    inn = normalize_inn(getattr(counterparty, "inn", None))
    if inn:
        return f"counterparty:inn:{inn}"

    name = (
        normalize_name(getattr(counterparty, "legal_name", None))
        or normalize_name(getattr(counterparty, "display_name", None))
        or "unknown"
    )
    email = normalize_email(getattr(counterparty, "primary_email", None)) or _first_normalized(
        getattr(counterparty, "emails", ()), normalize_email
    )
    phone = normalize_phone(getattr(counterparty, "primary_phone", None)) or _first_normalized(
        getattr(counterparty, "phones", ()), normalize_phone
    )
    website = normalize_website(getattr(counterparty, "primary_website", None)) or _first_normalized(
        getattr(counterparty, "websites", ()), normalize_website
    )
    contact_key = email or phone or website or "no-contact"
    return f"counterparty:fallback:{name}:{contact_key}"


def build_contact_dedup_key(contact: object) -> str:
    counterparty_id = str(getattr(contact, "counterparty_id", "")).strip() or "unknown"
    email = normalize_email(getattr(contact, "primary_email", None)) or _first_normalized(
        getattr(contact, "emails", ()), normalize_email
    )
    if email:
        return f"contact:{counterparty_id}:email:{email}"

    phone = normalize_phone(getattr(contact, "primary_phone", None)) or _first_normalized(
        getattr(contact, "phones", ()), normalize_phone
    )
    if phone:
        return f"contact:{counterparty_id}:phone:{phone}"

    name = normalize_name(getattr(contact, "full_name", None)) or "unknown"
    return f"contact:{counterparty_id}:name:{name}"


def _digits_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    return digits or None


def _first_normalized(values: Iterable[Optional[str]], normalizer) -> Optional[str]:
    for value in values:
        normalized = normalizer(value)
        if normalized:
            return normalized
    return None

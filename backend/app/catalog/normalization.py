from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Tuple


def normalize_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().lower().split())
    return normalized or None


def normalize_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = "".join(str(value).strip().upper().split())
    return normalized or None


def normalize_label(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    return normalized or None


def normalize_unit(value: Optional[str]) -> Optional[str]:
    normalized = normalize_label(value)
    return normalized.lower() if normalized else None


def normalize_currency(value: Optional[str]) -> Optional[str]:
    normalized = normalize_code(value)
    return normalized or None


def normalize_attribute_key(value: str) -> str:
    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def normalize_attribute_value(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_string_tuple(values: Iterable[str | None]) -> Tuple[str, ...]:
    result: list[str] = []
    for value in values:
        normalized = normalize_label(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result)


def freeze_string_mapping(mapping: Mapping[str, str] | None) -> Mapping[str, str]:
    return MappingProxyType(
        {
            str(key): str(value)
            for key, value in dict(mapping or {}).items()
            if str(key).strip() and str(value).strip()
        }
    )


def freeze_attributes(attributes: Mapping[str, Any] | None) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in dict(attributes or {}).items():
        normalized_key = normalize_attribute_key(str(key))
        if not normalized_key:
            continue
        frozen[normalized_key] = _freeze_json_value(value)
    return MappingProxyType(frozen)


def attributes_to_json(attributes: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _json_value(value) for key, value in attributes.items()}


def to_decimal(value: Decimal | int | float | str | None, *, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def decimal_to_json(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def build_catalog_item_dedup_key(item: Any) -> str:
    for field_name in ("article", "internal_code", "supplier_code", "sku"):
        value = normalize_code(getattr(item, field_name, None))
        if value:
            return f"{field_name}:{value}"
    name = normalize_name(getattr(item, "normalized_name", None) or getattr(item, "name", None)) or ""
    brand = normalize_name(getattr(item, "brand", None)) or ""
    manufacturer = normalize_name(getattr(item, "manufacturer", None)) or ""
    return f"name:{name}:brand:{brand}:manufacturer:{manufacturer}"


def build_stock_balance_key(balance: Any) -> str:
    warehouse = normalize_name(getattr(balance, "warehouse_ref", None)) or "default"
    return f"stock:{getattr(balance, 'catalog_item_id')}:{warehouse}"


def build_price_record_key(record: Any) -> str:
    supplier = normalize_name(getattr(record, "supplier_ref", None)) or "default"
    return (
        f"price:{getattr(record, 'catalog_item_id')}:"
        f"{getattr(record, 'price_type').value}:{getattr(record, 'currency')}:{supplier}"
    )


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json_value(inner) for key, inner in value.items()})
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, Decimal):
        return value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(inner) for key, inner in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, Decimal):
        return decimal_to_json(value)
    return value

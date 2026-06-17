from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .normalization import (
    attributes_to_json,
    decimal_to_json,
    freeze_attributes,
    freeze_string_mapping,
    normalize_code,
    normalize_currency,
    normalize_label,
    normalize_name,
    normalize_string_tuple,
    normalize_unit,
    to_decimal,
)
from .statuses import (
    CatalogItemStatus,
    CatalogSourceType,
    PriceType,
    coerce_catalog_item_status,
    coerce_catalog_source_type,
    coerce_price_type,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def empty_tuple() -> Tuple[str, ...]:
    return ()


def empty_attributes() -> Mapping[str, Any]:
    return MappingProxyType({})


def empty_external_refs() -> Mapping[str, str]:
    return MappingProxyType({})


@dataclass(frozen=True)
class CatalogItem:
    catalog_item_id: str
    name: str
    sku: Optional[str] = None
    article: Optional[str] = None
    supplier_code: Optional[str] = None
    internal_code: Optional[str] = None
    normalized_name: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    product_line: Optional[str] = None
    description: Optional[str] = None
    unit: str = "pcs"
    package_size: Optional[Decimal] = None
    attributes: Mapping[str, Any] = field(default_factory=empty_attributes)
    aliases: Tuple[str, ...] = field(default_factory=empty_tuple)
    search_terms: Tuple[str, ...] = field(default_factory=empty_tuple)
    status: CatalogItemStatus = CatalogItemStatus.ACTIVE
    source: Optional[CatalogSourceType] = None
    external_refs: Mapping[str, str] = field(default_factory=empty_external_refs)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "catalog_item_id", str(self.catalog_item_id))
        object.__setattr__(self, "name", normalize_label(self.name) or str(self.name).strip())
        for field_name in ("sku", "article", "supplier_code", "internal_code"):
            object.__setattr__(self, field_name, normalize_code(getattr(self, field_name)))
        object.__setattr__(self, "normalized_name", normalize_name(self.normalized_name) or normalize_name(self.name))
        for field_name in ("product_type", "category", "group", "subgroup", "brand", "manufacturer", "product_line"):
            object.__setattr__(self, field_name, normalize_label(getattr(self, field_name)))
        object.__setattr__(self, "description", normalize_label(self.description))
        object.__setattr__(self, "unit", normalize_unit(self.unit) or "pcs")
        object.__setattr__(self, "package_size", to_decimal(self.package_size))
        object.__setattr__(self, "attributes", freeze_attributes(self.attributes))
        object.__setattr__(self, "aliases", normalize_string_tuple(self.aliases))
        object.__setattr__(self, "search_terms", normalize_string_tuple(self.search_terms))
        object.__setattr__(self, "status", coerce_catalog_item_status(self.status))
        object.__setattr__(self, "source", coerce_catalog_source_type(self.source))
        object.__setattr__(self, "external_refs", freeze_string_mapping(self.external_refs))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"catalog_item:{self.catalog_item_id}"

    def with_status(self, status: CatalogItemStatus, *, updated_at: Optional[datetime] = None) -> "CatalogItem":
        return replace(self, status=coerce_catalog_item_status(status), updated_at=updated_at or utcnow())

    def with_updates(self, **changes: Any) -> "CatalogItem":
        changes.setdefault("updated_at", utcnow())
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_item_id": self.catalog_item_id,
            "ref": self.ref,
            "sku": self.sku,
            "article": self.article,
            "supplier_code": self.supplier_code,
            "internal_code": self.internal_code,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "product_type": self.product_type,
            "category": self.category,
            "group": self.group,
            "subgroup": self.subgroup,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "product_line": self.product_line,
            "description": self.description,
            "unit": self.unit,
            "package_size": decimal_to_json(self.package_size),
            "attributes": attributes_to_json(self.attributes),
            "aliases": list(self.aliases),
            "search_terms": list(self.search_terms),
            "status": self.status.value,
            "source": self.source.value if self.source else None,
            "external_refs": dict(self.external_refs),
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "catalog_item_id": self.catalog_item_id,
            "sku": self.sku,
            "article": self.article,
            "supplier_code": self.supplier_code,
            "internal_code": self.internal_code,
            "name": self.name,
            "product_type": self.product_type,
            "category": self.category,
            "group": self.group,
            "subgroup": self.subgroup,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "product_line": self.product_line,
            "description": self.description,
            "unit": self.unit,
            "package_size": decimal_to_json(self.package_size),
            "attributes": attributes_to_json(self.attributes),
            "aliases": list(self.aliases),
            "search_terms": list(self.search_terms),
            "status": self.status.value,
            "updated_at": _datetime_to_json(self.updated_at),
        }


@dataclass(frozen=True)
class StockBalance:
    stock_balance_id: str
    catalog_item_id: str
    warehouse_ref: str
    quantity_available: Decimal | int | float | str = Decimal("0")
    quantity_reserved: Decimal | int | float | str = Decimal("0")
    unit: str = "pcs"
    updated_at: datetime = field(default_factory=utcnow)
    source: Optional[CatalogSourceType] = None
    external_refs: Mapping[str, str] = field(default_factory=empty_external_refs)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stock_balance_id", str(self.stock_balance_id))
        object.__setattr__(self, "catalog_item_id", str(self.catalog_item_id))
        object.__setattr__(self, "warehouse_ref", normalize_label(self.warehouse_ref) or "default")
        object.__setattr__(self, "quantity_available", to_decimal(self.quantity_available, default=Decimal("0")))
        object.__setattr__(self, "quantity_reserved", to_decimal(self.quantity_reserved, default=Decimal("0")))
        object.__setattr__(self, "unit", normalize_unit(self.unit) or "pcs")
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))
        object.__setattr__(self, "source", coerce_catalog_source_type(self.source))
        object.__setattr__(self, "external_refs", freeze_string_mapping(self.external_refs))

    @property
    def ref(self) -> str:
        return f"stock_balance:{self.stock_balance_id}"

    @property
    def catalog_item_ref(self) -> str:
        return f"catalog_item:{self.catalog_item_id}"

    def with_updates(self, **changes: Any) -> "StockBalance":
        changes.setdefault("updated_at", utcnow())
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock_balance_id": self.stock_balance_id,
            "ref": self.ref,
            "catalog_item_id": self.catalog_item_id,
            "catalog_item_ref": self.catalog_item_ref,
            "warehouse_ref": self.warehouse_ref,
            "quantity_available": decimal_to_json(self.quantity_available),
            "quantity_reserved": decimal_to_json(self.quantity_reserved),
            "unit": self.unit,
            "updated_at": _datetime_to_json(self.updated_at),
            "source": self.source.value if self.source else None,
            "external_refs": dict(self.external_refs),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "stock_balance_id": self.stock_balance_id,
            "catalog_item_id": self.catalog_item_id,
            "warehouse_ref": self.warehouse_ref,
            "quantity_available": decimal_to_json(self.quantity_available),
            "quantity_reserved": decimal_to_json(self.quantity_reserved),
            "unit": self.unit,
            "updated_at": _datetime_to_json(self.updated_at),
        }


@dataclass(frozen=True)
class PriceRecord:
    price_record_id: str
    catalog_item_id: str
    price_type: PriceType | str
    currency: str
    amount: Decimal | int | float | str
    vat_rate: Decimal | int | float | str | None = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    supplier_ref: Optional[str] = None
    source: Optional[CatalogSourceType] = None
    external_refs: Mapping[str, str] = field(default_factory=empty_external_refs)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "price_record_id", str(self.price_record_id))
        object.__setattr__(self, "catalog_item_id", str(self.catalog_item_id))
        object.__setattr__(self, "price_type", coerce_price_type(self.price_type))
        object.__setattr__(self, "currency", normalize_currency(self.currency) or "RUB")
        object.__setattr__(self, "amount", to_decimal(self.amount, default=Decimal("0")))
        object.__setattr__(self, "vat_rate", to_decimal(self.vat_rate))
        object.__setattr__(self, "valid_from", None if self.valid_from is None else _coerce_datetime(self.valid_from))
        object.__setattr__(self, "valid_to", None if self.valid_to is None else _coerce_datetime(self.valid_to))
        object.__setattr__(self, "supplier_ref", normalize_label(self.supplier_ref))
        object.__setattr__(self, "source", coerce_catalog_source_type(self.source))
        object.__setattr__(self, "external_refs", freeze_string_mapping(self.external_refs))
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at))
        object.__setattr__(self, "updated_at", _coerce_datetime(self.updated_at))

    @property
    def ref(self) -> str:
        return f"price_record:{self.price_record_id}"

    @property
    def catalog_item_ref(self) -> str:
        return f"catalog_item:{self.catalog_item_id}"

    def with_updates(self, **changes: Any) -> "PriceRecord":
        changes.setdefault("updated_at", utcnow())
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "price_record_id": self.price_record_id,
            "ref": self.ref,
            "catalog_item_id": self.catalog_item_id,
            "catalog_item_ref": self.catalog_item_ref,
            "price_type": self.price_type.value,
            "currency": self.currency,
            "amount": decimal_to_json(self.amount),
            "vat_rate": decimal_to_json(self.vat_rate),
            "valid_from": _datetime_to_json(self.valid_from) if self.valid_from else None,
            "valid_to": _datetime_to_json(self.valid_to) if self.valid_to else None,
            "supplier_ref": self.supplier_ref,
            "source": self.source.value if self.source else None,
            "external_refs": dict(self.external_refs),
            "created_at": _datetime_to_json(self.created_at),
            "updated_at": _datetime_to_json(self.updated_at),
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "price_record_id": self.price_record_id,
            "catalog_item_id": self.catalog_item_id,
            "price_type": self.price_type.value,
            "currency": self.currency,
            "amount": decimal_to_json(self.amount),
            "vat_rate": decimal_to_json(self.vat_rate),
            "valid_from": _datetime_to_json(self.valid_from) if self.valid_from else None,
            "valid_to": _datetime_to_json(self.valid_to) if self.valid_to else None,
            "updated_at": _datetime_to_json(self.updated_at),
        }


@dataclass(frozen=True)
class CatalogCardView:
    catalog_item_id: str
    display_name: str
    article: Optional[str]
    sku: Optional[str]
    supplier_code: Optional[str]
    product_type: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    manufacturer: Optional[str]
    availability_summary: Mapping[str, Any]
    price_summary: Mapping[str, Any]
    highlights: Mapping[str, Any]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_item_id": self.catalog_item_id,
            "display_name": self.display_name,
            "article": self.article,
            "sku": self.sku,
            "supplier_code": self.supplier_code,
            "product_type": self.product_type,
            "category": self.category,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "availability_summary": dict(self.availability_summary),
            "price_summary": dict(self.price_summary),
            "highlights": dict(self.highlights),
            "status": self.status,
        }


@dataclass(frozen=True)
class CatalogListRow:
    catalog_item_id: str
    article: Optional[str]
    internal_code: Optional[str]
    supplier_code: Optional[str]
    name: str
    product_type: Optional[str]
    category: Optional[str]
    group: Optional[str]
    subgroup: Optional[str]
    brand: Optional[str]
    manufacturer: Optional[str]
    unit: str
    available_quantity: str
    base_price: Optional[str]
    currency: Optional[str]
    status: str
    source: Optional[str]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_item_id": self.catalog_item_id,
            "article": self.article,
            "internal_code": self.internal_code,
            "supplier_code": self.supplier_code,
            "name": self.name,
            "product_type": self.product_type,
            "category": self.category,
            "group": self.group,
            "subgroup": self.subgroup,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "unit": self.unit,
            "available_quantity": self.available_quantity,
            "base_price": self.base_price,
            "currency": self.currency,
            "status": self.status,
            "source": self.source,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class CatalogFacetSummary:
    categories: Mapping[str, int]
    product_types: Mapping[str, int]
    brands: Mapping[str, int]
    manufacturers: Mapping[str, int]
    statuses: Mapping[str, int]
    sources: Mapping[str, int]
    availability: Mapping[str, int]

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {
            "categories": dict(self.categories),
            "product_types": dict(self.product_types),
            "brands": dict(self.brands),
            "manufacturers": dict(self.manufacturers),
            "statuses": dict(self.statuses),
            "sources": dict(self.sources),
            "availability": dict(self.availability),
        }


def _coerce_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("datetime value expected")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _datetime_to_json(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .normalization import (
    normalize_attribute_key,
    normalize_attribute_value,
    normalize_currency,
    normalize_label,
    normalize_name,
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


class CatalogSort(str, Enum):
    RELEVANCE = "relevance"
    NAME = "name"
    ARTICLE = "article"
    AVAILABILITY = "availability"
    PRICE = "price"
    UPDATED_AT = "updated_at"


class CatalogViewMode(str, Enum):
    DASHBOARD = "dashboard"
    REFERENCE = "reference"


@dataclass(frozen=True)
class CatalogFilter:
    query: Optional[str] = None
    product_types: Tuple[str, ...] = field(default_factory=tuple)
    categories: Tuple[str, ...] = field(default_factory=tuple)
    groups: Tuple[str, ...] = field(default_factory=tuple)
    subgroups: Tuple[str, ...] = field(default_factory=tuple)
    brands: Tuple[str, ...] = field(default_factory=tuple)
    manufacturers: Tuple[str, ...] = field(default_factory=tuple)
    units: Tuple[str, ...] = field(default_factory=tuple)
    statuses: Tuple[CatalogItemStatus, ...] = field(default_factory=tuple)
    sources: Tuple[CatalogSourceType, ...] = field(default_factory=tuple)
    supplier_refs: Tuple[str, ...] = field(default_factory=tuple)
    has_stock: Optional[bool] = None
    min_available_quantity: Optional[Decimal] = None
    has_price: Optional[bool] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    currency: Optional[str] = None
    price_type: Optional[PriceType] = None
    attribute_filters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", normalize_name(self.query))
        for field_name in ("product_types", "categories", "groups", "subgroups", "brands", "manufacturers"):
            object.__setattr__(self, field_name, _normalize_name_tuple(getattr(self, field_name)))
        object.__setattr__(self, "units", tuple(value for value in (normalize_unit(unit) for unit in self.units) if value))
        object.__setattr__(self, "statuses", tuple(coerce_catalog_item_status(status) for status in self.statuses))
        object.__setattr__(
            self,
            "sources",
            tuple(source for source in (coerce_catalog_source_type(source) for source in self.sources) if source),
        )
        object.__setattr__(
            self,
            "supplier_refs",
            tuple(value for value in (normalize_label(ref) for ref in self.supplier_refs) if value),
        )
        object.__setattr__(self, "min_available_quantity", to_decimal(self.min_available_quantity))
        object.__setattr__(self, "min_price", to_decimal(self.min_price))
        object.__setattr__(self, "max_price", to_decimal(self.max_price))
        object.__setattr__(self, "currency", normalize_currency(self.currency))
        object.__setattr__(self, "price_type", None if self.price_type is None else coerce_price_type(self.price_type))
        object.__setattr__(self, "attribute_filters", _freeze_attribute_filters(self.attribute_filters))


@dataclass(frozen=True)
class CatalogQuery:
    filters: CatalogFilter = field(default_factory=CatalogFilter)
    sort: CatalogSort = CatalogSort.RELEVANCE
    view_mode: CatalogViewMode = CatalogViewMode.REFERENCE
    limit: Optional[int] = None
    offset: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "sort", coerce_catalog_sort(self.sort))
        object.__setattr__(self, "view_mode", coerce_catalog_view_mode(self.view_mode))
        object.__setattr__(self, "offset", max(0, int(self.offset)))
        if self.limit is not None:
            object.__setattr__(self, "limit", max(0, int(self.limit)))


def coerce_catalog_sort(sort: CatalogSort | str) -> CatalogSort:
    if isinstance(sort, CatalogSort):
        return sort
    return CatalogSort(str(sort))


def coerce_catalog_view_mode(view_mode: CatalogViewMode | str) -> CatalogViewMode:
    if isinstance(view_mode, CatalogViewMode):
        return view_mode
    return CatalogViewMode(str(view_mode))


def filter_value_matches(candidate: Any, expected: Any) -> bool:
    candidate_value = normalize_attribute_value(candidate)
    if isinstance(expected, (list, tuple, set, frozenset)):
        return candidate_value in {normalize_attribute_value(value) for value in expected}
    return candidate_value == normalize_attribute_value(expected)


def normalized_attr_filters(filters: Mapping[str, Any]) -> Mapping[str, Any]:
    return _freeze_attribute_filters(filters)


def _normalize_name_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        normalized = normalize_name(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result)


def _freeze_attribute_filters(filters: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            normalize_attribute_key(key): value
            for key, value in dict(filters or {}).items()
            if normalize_attribute_key(key)
        }
    )

from __future__ import annotations

from enum import Enum


class CatalogItemStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    BLOCKED = "blocked"


class CatalogSourceType(str, Enum):
    MANUAL = "manual"
    IMPORTED = "imported"
    ROSMA = "rosma"
    ARTMATICA = "artmatica"
    STOCK_FILE = "stock_file"


class PriceType(str, Enum):
    BASE = "base"
    RETAIL = "retail"
    PURCHASE = "purchase"
    SUPPLIER = "supplier"


def coerce_catalog_item_status(status: CatalogItemStatus | str) -> CatalogItemStatus:
    if isinstance(status, CatalogItemStatus):
        return status
    return CatalogItemStatus(str(status))


def coerce_catalog_source_type(source: CatalogSourceType | str | None) -> CatalogSourceType | None:
    if source is None:
        return None
    if isinstance(source, CatalogSourceType):
        return source
    return CatalogSourceType(str(source))


def coerce_price_type(price_type: PriceType | str) -> PriceType:
    if isinstance(price_type, PriceType):
        return price_type
    return PriceType(str(price_type))

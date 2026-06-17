"""Backend-only catalog, stock and price foundation."""

from .filtering import CatalogFilter, CatalogQuery, CatalogSort, CatalogViewMode
from .models import CatalogCardView, CatalogFacetSummary, CatalogItem, CatalogListRow, PriceRecord, StockBalance
from .normalization import (
    build_catalog_item_dedup_key,
    build_price_record_key,
    build_stock_balance_key,
    normalize_attribute_key,
    normalize_attribute_value,
    normalize_code,
    normalize_currency,
    normalize_name,
    normalize_unit,
)
from .repository import InMemoryCatalogRepository, RepositoryResult
from .statuses import CatalogItemStatus, CatalogSourceType, PriceType

__all__ = [
    "CatalogCardView",
    "CatalogFacetSummary",
    "CatalogFilter",
    "CatalogItem",
    "CatalogItemStatus",
    "CatalogListRow",
    "CatalogQuery",
    "CatalogSort",
    "CatalogSourceType",
    "CatalogViewMode",
    "InMemoryCatalogRepository",
    "PriceRecord",
    "PriceType",
    "RepositoryResult",
    "StockBalance",
    "build_catalog_item_dedup_key",
    "build_price_record_key",
    "build_stock_balance_key",
    "normalize_attribute_key",
    "normalize_attribute_value",
    "normalize_code",
    "normalize_currency",
    "normalize_name",
    "normalize_unit",
]

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class PriceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PriceSourceRef:
    """Reference to a price source or publication."""

    price_source_id: str
    source_version: Optional[str] = None


@dataclass(frozen=True)
class CatalogItemPriceRef:
    """Reference to a price entry for a catalog item."""

    catalog_item_price_id: str
    catalog_item_id: str
    price_source_ref: Optional[PriceSourceRef] = None
    status: PriceStatus = PriceStatus.UNKNOWN


@dataclass
class ManagerItemDiscount:
    """Manager-provided discount request boundary."""

    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    reason: Optional[str] = None


@dataclass
class CartItemPriceSnapshot:
    """Immutable future cart price snapshot boundary."""

    cart_item_ref: str
    catalog_item_id: str
    catalog_item_price_ref: Optional[CatalogItemPriceRef] = None
    manager_discount: Optional[ManagerItemDiscount] = None
    snapshot_data: Dict[str, Any] = field(default_factory=dict)

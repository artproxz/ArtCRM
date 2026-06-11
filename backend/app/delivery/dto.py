from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DeliveryStatus(str, Enum):
    UNKNOWN = "unknown"
    ESTIMATED = "estimated"
    SUPPLIER_CONFIRMED = "supplier_confirmed"
    MANUAL_CHECK_REQUIRED = "manual_check_required"


@dataclass
class DeliveryEstimateRequest:
    """Input boundary for future delivery estimation."""

    catalog_item_id: str
    manufacturer_scope: Optional[str] = None
    stock_status: Optional[str] = None


@dataclass
class CartItemDeliveryEstimate:
    """Future cart item delivery estimate boundary."""

    cart_item_ref: str
    customer_delivery_label: Optional[str] = None
    manager_delivery_label: Optional[str] = None
    estimate_source: Optional[str] = None
    supplier_confirmed_delivery_date: Optional[str] = None


@dataclass
class DeliveryEstimateResult:
    """Output boundary for future delivery estimation."""

    status: DeliveryStatus = DeliveryStatus.UNKNOWN
    estimate: Optional[CartItemDeliveryEstimate] = None
    warnings: List[str] = field(default_factory=list)

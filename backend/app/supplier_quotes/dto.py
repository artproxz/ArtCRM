from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SupplierQuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    WAITING_RESPONSE = "waiting_response"
    ANSWERED = "answered"
    CLOSED = "closed"
    CANCELED = "canceled"


@dataclass
class SupplierQuoteRequestItem:
    """Boundary item for a future supplier quote request draft."""

    catalog_item_id: Optional[str] = None
    full_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    related_component_type: Optional[str] = None
    service_type: Optional[str] = None


@dataclass
class SupplierQuoteRequest:
    """Supplier quote request draft boundary; sending email is out of scope."""

    manufacturer_scope: str
    request_card_ref: Optional[str] = None
    cart_ref: Optional[str] = None
    items: List[SupplierQuoteRequestItem] = field(default_factory=list)
    status: SupplierQuoteStatus = SupplierQuoteStatus.DRAFT
    draft_body: Optional[str] = None


@dataclass
class SupplierQuoteResponseItem:
    """Boundary item for a manually registered future supplier response."""

    catalog_item_id: Optional[str] = None
    confirmed_delivery_label: Optional[str] = None
    confirmed_available_qty: Optional[float] = None
    response_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupplierQuoteResponse:
    """Supplier quote response boundary; parsing logic is out of scope."""

    supplier_quote_request_id: str
    status: SupplierQuoteStatus = SupplierQuoteStatus.ANSWERED
    items: List[SupplierQuoteResponseItem] = field(default_factory=list)
    response_summary: Optional[str] = None

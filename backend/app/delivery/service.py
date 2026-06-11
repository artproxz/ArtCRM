from __future__ import annotations

from typing import Optional

from .dto import CartItemDeliveryEstimate, DeliveryEstimateRequest, DeliveryEstimateResult


class DeliveryEstimateService:
    """Delivery estimate boundary.

    Foundation only: no supplier response parsing or external delivery lookup is implemented here.
    """

    def estimate_delivery(self, request: DeliveryEstimateRequest) -> DeliveryEstimateResult:
        raise NotImplementedError("Delivery estimation is not implemented in ART-CATALOG-006.")

    def apply_supplier_confirmed_delivery(
        self,
        cart_item_ref: str,
        confirmed_delivery_label: str,
        confirmed_delivery_date: Optional[str] = None,
    ) -> CartItemDeliveryEstimate:
        raise NotImplementedError("Supplier-confirmed delivery application is not implemented in ART-CATALOG-006.")

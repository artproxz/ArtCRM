from __future__ import annotations

from .dto import CatalogItemPriceRef, CartItemPriceSnapshot, ManagerItemDiscount


class PricingService:
    """Pricing boundary.

    Foundation only: no price calculation or catalog identity mutation is implemented here.
    """

    def get_catalog_item_price(self, catalog_item_id: str) -> CatalogItemPriceRef:
        raise NotImplementedError("Catalog item price lookup is not implemented in ART-CATALOG-006.")

    def create_cart_price_snapshot(self, catalog_item_id: str, quantity: float) -> CartItemPriceSnapshot:
        raise NotImplementedError("Cart price snapshot creation is not implemented in ART-CATALOG-006.")

    def apply_manager_discount(self, cart_item_ref: str, discount: ManagerItemDiscount) -> CartItemPriceSnapshot:
        raise NotImplementedError("Manager discount application is not implemented in ART-CATALOG-006.")

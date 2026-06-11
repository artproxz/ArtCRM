from __future__ import annotations

from .dto import SupplierQuoteRequest, SupplierQuoteResponse


class SupplierQuoteService:
    """Supplier quote boundary.

    Foundation only: this service must not send email or call supplier integrations.
    """

    def create_quote_request_draft(self, request: SupplierQuoteRequest) -> SupplierQuoteRequest:
        raise NotImplementedError("Supplier quote draft creation is not implemented in ART-CATALOG-006.")

    def register_supplier_response(self, response: SupplierQuoteResponse) -> SupplierQuoteResponse:
        raise NotImplementedError("Supplier quote response registration is not implemented in ART-CATALOG-006.")

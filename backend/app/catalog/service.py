from __future__ import annotations

from .dto import CatalogItemRef, CatalogLookupRequest, CatalogLookupResult, CatalogPublicationRef


class CatalogService:
    """Catalog lookup boundary.

    Foundation only: no catalog lookup, persistence, parser, or integration logic is implemented here.
    """

    def get_active_publication(self, manufacturer_scope: str) -> CatalogPublicationRef:
        raise NotImplementedError("Catalog publication lookup is not implemented in ART-CATALOG-006.")

    def find_catalog_candidates(self, request: CatalogLookupRequest) -> CatalogLookupResult:
        raise NotImplementedError("Catalog candidate lookup is not implemented in ART-CATALOG-006.")

    def get_catalog_item(self, catalog_item_id: str) -> CatalogItemRef:
        raise NotImplementedError("Catalog item lookup is not implemented in ART-CATALOG-006.")

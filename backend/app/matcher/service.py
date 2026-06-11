from __future__ import annotations

from .dto import CatalogMatchRequest, CatalogMatchResponse


class CatalogMatcherService:
    """Backend Catalog Matcher boundary.

    Foundation only: matching decisions and algorithms are intentionally not implemented here.
    """

    def match_position(self, request: CatalogMatchRequest) -> CatalogMatchResponse:
        raise NotImplementedError("Catalog matching is not implemented in ART-CATALOG-006.")

from __future__ import annotations

from .dto import StockLookupRequest, StockLookupResult, StockSnapshotRef


class StockService:
    """Stock lookup boundary.

    Foundation only: stock data does not create or mutate catalog identity here.
    """

    def get_latest_stock_snapshot(self, manufacturer_scope: str) -> StockSnapshotRef:
        raise NotImplementedError("Stock snapshot lookup is not implemented in ART-CATALOG-006.")

    def get_stock_for_catalog_item(self, request: StockLookupRequest) -> StockLookupResult:
        raise NotImplementedError("Stock lookup is not implemented in ART-CATALOG-006.")

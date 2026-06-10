"""Stock module boundary for ArtCRM backend."""

from .dto import StockLookupRequest, StockLookupResult, StockSnapshotRef, StockStatus
from .service import StockService

__all__ = [
    "StockLookupRequest",
    "StockLookupResult",
    "StockService",
    "StockSnapshotRef",
    "StockStatus",
]

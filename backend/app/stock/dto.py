from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    RESERVED_ONLY = "reserved_only"
    EXPECTED = "expected"
    UNKNOWN = "unknown"
    QUOTE_BASED = "quote_based"
    MANUAL_CHECK_REQUIRED = "manual_check_required"
    UNRESOLVED_STOCK_REFERENCE = "unresolved_stock_reference"


@dataclass(frozen=True)
class StockSnapshotRef:
    """Reference to an imported stock snapshot."""

    stock_snapshot_id: str
    snapshot_version: Optional[str] = None


@dataclass
class StockLookupRequest:
    """Input boundary for future stock lookup by catalog item."""

    catalog_item_id: str
    manufacturer_scope: str
    warehouse_code: Optional[str] = None
    stock_snapshot_ref: Optional[StockSnapshotRef] = None


@dataclass
class StockLookupResult:
    """Output boundary for future stock lookup."""

    stock_status: StockStatus = StockStatus.UNKNOWN
    stock_snapshot_ref: Optional[StockSnapshotRef] = None
    availability: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

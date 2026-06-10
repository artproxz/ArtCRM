from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CatalogItemRef:
    """Reference to a catalog item without loading catalog data."""

    catalog_item_id: str
    display_name: Optional[str] = None


@dataclass(frozen=True)
class CatalogPublicationRef:
    """Reference to a published catalog version."""

    catalog_publication_id: str
    publication_version: Optional[str] = None


@dataclass
class CatalogLookupRequest:
    """Input boundary for future catalog candidate lookup."""

    manufacturer_scope: str
    product_type: Optional[str] = None
    normalized_name: Optional[str] = None
    source_code: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    catalog_publication_ref: Optional[CatalogPublicationRef] = None


@dataclass
class CatalogLookupResult:
    """Output boundary for future catalog candidate lookup."""

    catalog_publication_ref: Optional[CatalogPublicationRef] = None
    candidates: List[CatalogItemRef] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

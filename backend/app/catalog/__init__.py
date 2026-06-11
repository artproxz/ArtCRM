"""Catalog module boundary for ArtCRM backend."""

from .dto import CatalogItemRef, CatalogLookupRequest, CatalogLookupResult, CatalogPublicationRef
from .service import CatalogService

__all__ = [
    "CatalogItemRef",
    "CatalogLookupRequest",
    "CatalogLookupResult",
    "CatalogPublicationRef",
    "CatalogService",
]

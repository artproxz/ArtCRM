"""Matcher module boundary for ArtCRM backend."""

from .dto import (
    CatalogMatchDecision,
    CatalogMatchRequest,
    CatalogMatchResponse,
    MatcherExecutionRef,
    MatcherValidationError,
)
from .service import CatalogMatcherService

__all__ = [
    "CatalogMatchDecision",
    "CatalogMatchRequest",
    "CatalogMatchResponse",
    "CatalogMatcherService",
    "MatcherExecutionRef",
    "MatcherValidationError",
]

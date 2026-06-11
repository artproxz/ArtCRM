from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CatalogMatchDecision(str, Enum):
    EXACT = "exact"
    COMPATIBLE_EXACT = "compatible_exact"
    ANALOG_CANDIDATE = "analog_candidate"
    NEEDS_REVIEW = "needs_review"
    NO_MATCH = "no_match"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MatcherExecutionRef:
    """Reference to a future matcher execution audit record."""

    matcher_execution_id: str
    matcher_version: Optional[str] = None


@dataclass
class MatcherValidationError:
    """Validation error boundary for future matcher execution."""

    error_code: str
    error_message: str
    field: Optional[str] = None
    retryable: bool = False


@dataclass
class CatalogMatchRequest:
    """Input boundary for backend-only catalog matching."""

    request_id: str
    request_position_ref: str
    product_type: str
    manufacturer_scope: str
    structured_intent: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    catalog_publication_ref: Optional[str] = None
    stock_snapshot_ref: Optional[str] = None


@dataclass
class CatalogMatchResponse:
    """Output boundary for backend-only catalog matching."""

    request_id: str
    decision: CatalogMatchDecision = CatalogMatchDecision.NEEDS_REVIEW
    selected_catalog_item_id: Optional[str] = None
    manager_message: Optional[str] = None
    errors: List[MatcherValidationError] = field(default_factory=list)
    matcher_execution_ref: Optional[MatcherExecutionRef] = None

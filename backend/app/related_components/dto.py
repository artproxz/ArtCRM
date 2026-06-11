from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RelatedComponentDecision(str, Enum):
    ACCEPTED_CANDIDATE = "accepted_candidate"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"
    NOT_REQUESTED = "not_requested"


@dataclass(frozen=True)
class RelatedComponentRuleRef:
    """Reference to a future related component validation rule."""

    related_component_rule_id: str
    rule_version: Optional[str] = None


@dataclass
class RelatedComponentValidationRequest:
    """Input boundary for backend validation of related component suggestions."""

    parent_position_ref: str
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    manufacturer_scope: Optional[str] = None


@dataclass
class RelatedComponentValidationResult:
    """Output boundary for related component validation."""

    decision: RelatedComponentDecision = RelatedComponentDecision.NEEDS_REVIEW
    rule_refs: List[RelatedComponentRuleRef] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    manager_message: Optional[str] = None

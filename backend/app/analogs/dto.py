from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalogDecision(str, Enum):
    NOT_REQUESTED = "not_requested"
    UNAVAILABLE = "unavailable"
    CANDIDATE_FOUND = "candidate_found"
    BLOCKED = "blocked"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class AnalogRuleRef:
    """Reference to a future analog rule."""

    analog_rule_id: str
    rule_version: Optional[str] = None


@dataclass
class AnalogLookupRequest:
    """Input boundary for future analog candidate lookup."""

    product_type: str
    structured_intent: Dict[str, Any] = field(default_factory=dict)
    manufacturer_scope: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalogLookupResult:
    """Output boundary for future analog candidate lookup."""

    decision: AnalogDecision = AnalogDecision.UNAVAILABLE
    analog_rule_refs: List[AnalogRuleRef] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

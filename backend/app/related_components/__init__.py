"""Related components module boundary for ArtCRM backend."""

from .dto import (
    RelatedComponentDecision,
    RelatedComponentRuleRef,
    RelatedComponentValidationRequest,
    RelatedComponentValidationResult,
)
from .service import RelatedComponentService

__all__ = [
    "RelatedComponentDecision",
    "RelatedComponentRuleRef",
    "RelatedComponentService",
    "RelatedComponentValidationRequest",
    "RelatedComponentValidationResult",
]

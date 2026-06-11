from __future__ import annotations

from .dto import RelatedComponentValidationRequest, RelatedComponentValidationResult


class RelatedComponentService:
    """Related component validation boundary.

    Foundation only: candidate suggestions are not approved or added to documents here.
    """

    def validate_related_components(
        self,
        request: RelatedComponentValidationRequest,
    ) -> RelatedComponentValidationResult:
        raise NotImplementedError("Related component validation is not implemented in ART-CATALOG-006.")

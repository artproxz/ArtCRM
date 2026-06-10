from __future__ import annotations

from .dto import AnalogLookupRequest, AnalogLookupResult


class AnalogRuleService:
    """Analog rule lookup boundary.

    Foundation only: analog matching rules are intentionally not implemented here.
    """

    def find_analog_candidates(self, request: AnalogLookupRequest) -> AnalogLookupResult:
        raise NotImplementedError("Analog candidate lookup is not implemented in ART-CATALOG-006.")

"""Analogs module boundary for ArtCRM backend."""

from .dto import AnalogDecision, AnalogLookupRequest, AnalogLookupResult, AnalogRuleRef
from .service import AnalogRuleService

__all__ = [
    "AnalogDecision",
    "AnalogLookupRequest",
    "AnalogLookupResult",
    "AnalogRuleRef",
    "AnalogRuleService",
]

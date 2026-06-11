from __future__ import annotations

from .dto import AuditEvent, MatcherExecutionAuditRef


class AuditService:
    """Audit boundary.

    Foundation only: no persistence, log sink, or external audit integration is implemented here.
    """

    def record_event(self, event: AuditEvent) -> AuditEvent:
        raise NotImplementedError("Audit event recording is not implemented in ART-CATALOG-006.")

    def record_matcher_execution(
        self,
        matcher_execution_ref: MatcherExecutionAuditRef,
    ) -> MatcherExecutionAuditRef:
        raise NotImplementedError("Matcher execution audit recording is not implemented in ART-CATALOG-006.")

from datetime import datetime, timezone
from types import MappingProxyType
import unittest

from backend.app.audit import (
    AuditEventCategory,
    AuditEventResult,
    AuditService,
    AuditSeverity,
    REDACTED_VALUE,
)
from backend.app.auth.permissions import ActorContext, ActorType


DEMO_TIMESTAMP = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


class AuditEventServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AuditService(clock=lambda: DEMO_TIMESTAMP)
        self.actor = ActorContext(actor_type=ActorType.STAFF_USER, actor_id="user:demo-manager")

    def test_appending_mutation_event_creates_event_with_id_and_timestamp(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="request.updated",
            entity_type="request",
            entity_ref="request:demo",
            action="update",
        )

        self.assertEqual(event.event_id, "audit_event:000001")
        self.assertEqual(event.timestamp, DEMO_TIMESTAMP)
        self.assertEqual(event.event_category, AuditEventCategory.MUTATION)

    def test_appending_sensitive_read_event_uses_sensitive_read_category(self):
        event = self.service.record_sensitive_read(
            actor=self.actor,
            event_name="pricing.margin_viewed",
            entity_type="quote",
            entity_ref="quote:demo",
        )

        self.assertEqual(event.event_category, AuditEventCategory.SENSITIVE_READ)
        self.assertEqual(event.severity, AuditSeverity.HIGH)

    def test_event_records_actor_type_and_actor_id_from_context(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="quote.created",
            entity_type="quote",
            entity_ref="quote:demo",
            action="create",
        )

        self.assertEqual(event.actor_type, ActorType.STAFF_USER)
        self.assertEqual(event.actor_id, "user:demo-manager")

    def test_event_records_entity_type_and_entity_ref(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="document.linked",
            entity_type="document",
            entity_ref="document:demo",
            action="link",
        )

        self.assertEqual(event.entity_type, "document")
        self.assertEqual(event.entity_ref, "document:demo")

    def test_event_records_source_module(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="quote.created",
            entity_type="quote",
            entity_ref="quote:demo",
            action="create",
            source_module="quote_service",
        )

        self.assertEqual(event.source_module, "quote_service")

    def test_event_records_correlation_id_and_idempotency_key(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="quote.created",
            entity_type="quote",
            entity_ref="quote:demo",
            action="create",
            correlation_id="correlation:demo",
            idempotency_key="idempotency:demo",
            request_id="request-id:demo",
        )

        self.assertEqual(event.correlation_id, "correlation:demo")
        self.assertEqual(event.idempotency_key, "idempotency:demo")
        self.assertEqual(event.request_id, "request-id:demo")

    def test_payload_sanitizer_redacts_obvious_secret_keys(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="permission.granted",
            entity_type="permission",
            entity_ref="permission:demo",
            action="grant",
            payload={"password": "demo-password", "api_key": "demo-api-key"},
        )

        self.assertEqual(event.safe_payload["password"], REDACTED_VALUE)
        self.assertEqual(event.safe_payload["api_key"], REDACTED_VALUE)

    def test_payload_sanitizer_redacts_nested_secret_keys(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="agent_run.completed",
            entity_type="agent_run",
            entity_ref="agent_run:demo",
            action="complete",
            payload={"nested": {"refresh_token": "demo-refresh-token"}},
        )

        self.assertEqual(event.safe_payload["nested"]["refresh_token"], REDACTED_VALUE)

    def test_raw_prompt_token_client_secret_and_authorization_are_not_stored(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="agent_run.failed",
            entity_type="agent_run",
            entity_ref="agent_run:demo",
            action="fail",
            payload={
                "raw_prompt": "full prompt text",
                "token": "demo-token",
                "client_secret": "demo-client-secret",
                "authorization": "Bearer demo",
                "raw_llm_response": "full raw response",
            },
        )

        for key in ("raw_prompt", "token", "client_secret", "authorization", "raw_llm_response"):
            self.assertEqual(event.safe_payload[key], REDACTED_VALUE)

    def test_safe_payload_keeps_non_sensitive_metadata(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="counterparty_import.previewed",
            entity_type="counterparty_import",
            entity_ref="import:demo",
            action="preview",
            result=AuditEventResult.PREVIEWED,
            payload={"rows_total": 10, "rows_ready": 8},
            severity=AuditSeverity.MEDIUM,
        )

        self.assertEqual(event.safe_payload["rows_total"], 10)
        self.assertEqual(event.safe_payload["rows_ready"], 8)
        self.assertEqual(event.result, AuditEventResult.PREVIEWED)

    def test_in_memory_store_is_append_only_from_caller_perspective(self):
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:demo",
            action="create",
            payload={"safe": "value"},
        )
        first_snapshot = self.service.list_events()

        self.service.record_mutation(
            actor=self.actor,
            event_name="request.updated",
            entity_type="request",
            entity_ref="request:demo",
            action="update",
        )

        self.assertIsInstance(first_snapshot, tuple)
        self.assertEqual(len(first_snapshot), 1)
        self.assertIsInstance(first_snapshot[0].safe_payload, MappingProxyType)
        with self.assertRaises(TypeError):
            first_snapshot[0].safe_payload["safe"] = "changed"
        self.assertEqual(len(self.service.list_events()), 2)

    def test_list_by_entity_returns_only_matching_entity_events(self):
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:one",
            action="create",
        )
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:two",
            action="create",
        )

        events = self.service.list_by_entity("request", "request:one")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_ref, "request:one")

    def test_list_by_actor_returns_only_matching_actor_events(self):
        other_actor = ActorContext(actor_type=ActorType.STAFF_USER, actor_id="user:other")
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:one",
            action="create",
        )
        self.service.record_mutation(
            actor=other_actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:two",
            action="create",
        )

        events = self.service.list_by_actor("user:demo-manager")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].actor_id, "user:demo-manager")

    def test_list_by_correlation_id_returns_only_matching_events(self):
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:one",
            action="create",
            correlation_id="correlation:one",
        )
        self.service.record_mutation(
            actor=self.actor,
            event_name="request.created",
            entity_type="request",
            entity_ref="request:two",
            action="create",
            correlation_id="correlation:two",
        )

        events = self.service.list_by_correlation_id("correlation:one")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].correlation_id, "correlation:one")

    def test_unknown_or_anonymous_actor_can_be_audited_safely(self):
        for actor_type in (ActorType.UNKNOWN, ActorType.ANONYMOUS):
            with self.subTest(actor_type=actor_type):
                event = self.service.record_sensitive_read(
                    actor=ActorContext(actor_type=actor_type),
                    event_name="permission.denied",
                    entity_type="permission",
                    entity_ref="permission:demo",
                    result=AuditEventResult.DENIED,
                )

                self.assertEqual(event.actor_type, actor_type)
                self.assertIsNone(event.actor_id)
                self.assertEqual(event.result, AuditEventResult.DENIED)

    def test_safe_explanation_and_metadata_do_not_leak_sensitive_payloads(self):
        event = self.service.record_mutation(
            actor=self.actor,
            event_name="agent_run.failed",
            entity_type="agent_run",
            entity_ref="agent_run:demo",
            action="fail",
            payload={
                "safe_summary": "Agent failed with redacted runtime error.",
                "full_prompt": "do not store this prompt",
                "details": {"private_key": "do not store key"},
            },
            safe_explanation="Agent failed with redacted runtime error.",
        )

        self.assertEqual(event.safe_explanation, "Agent failed with redacted runtime error.")
        self.assertEqual(event.safe_payload["safe_summary"], "Agent failed with redacted runtime error.")
        self.assertEqual(event.safe_payload["full_prompt"], REDACTED_VALUE)
        self.assertEqual(event.safe_payload["details"]["private_key"], REDACTED_VALUE)


if __name__ == "__main__":
    unittest.main()

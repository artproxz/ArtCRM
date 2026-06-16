import json
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

from backend.app.common import ErrorCode
from backend.app.request_cards import (
    InMemoryRequestRepository,
    RequestCard,
    RequestPosition,
    RequestPositionStatus,
    RequestPriority,
    RequestSourceType,
    RequestStatus,
)
from backend.app.workflow import TransitionDecisionReason


class RequestCardPositionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryRequestRepository()

    def test_request_card_can_be_created_with_stable_id_and_ref(self):
        card = RequestCard(request_id="demo-001", title="Demo request")

        result = self.repository.create_request(card)

        self.assertTrue(result.success)
        self.assertEqual(result.value.request_id, "demo-001")
        self.assertEqual(result.value.ref, "request:demo-001")

    def test_request_card_defaults_are_sane(self):
        card = RequestCard(request_id="demo-001")

        self.assertEqual(card.status, RequestStatus.DRAFT)
        self.assertEqual(card.source_type, RequestSourceType.UNKNOWN)
        self.assertEqual(card.priority, RequestPriority.NORMAL)
        self.assertEqual(card.position_refs, ())

    def test_request_position_can_be_created_with_source_text_quantity_and_unit(self):
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="5 pcs pressure gauge",
            quantity="5",
            unit="pcs",
        )

        self.assertEqual(position.position_id, "pos-001")
        self.assertEqual(position.request_id, "demo-001")
        self.assertEqual(position.quantity, 5)
        self.assertEqual(position.unit, "pcs")
        self.assertEqual(position.status, RequestPositionStatus.NEW)

    def test_position_can_be_added_to_request_repository(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
        )

        result = self.repository.add_position(position)
        request = self.repository.get_request("demo-001").value

        self.assertTrue(result.success)
        self.assertEqual(request.position_refs, ("request_position:pos-001",))

    def test_repository_can_get_request_by_id(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.get_request("demo-001")

        self.assertTrue(result.success)
        self.assertEqual(result.value.request_id, "demo-001")

    def test_repository_can_list_requests(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.create_request(RequestCard(request_id="demo-002"))

        requests = self.repository.list_requests()

        self.assertEqual(len(requests), 2)
        self.assertEqual({request.request_id for request in requests}, {"demo-001", "demo-002"})

    def test_repository_can_list_positions_by_request(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.add_position(
            RequestPosition(position_id="pos-002", request_id="demo-001", line_no=2, source_text="Second")
        )
        self.repository.add_position(
            RequestPosition(position_id="pos-001", request_id="demo-001", line_no=1, source_text="First")
        )

        result = self.repository.list_positions_by_request("demo-001")

        self.assertTrue(result.success)
        self.assertEqual([position.position_id for position in result.value], ["pos-001", "pos-002"])

    def test_updating_request_status_uses_state_transition_guard(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.READY_FOR_MATCHING,
            actor_permissions={"request.change_status"},
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.transition_decision)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.ALLOWED_TRANSITION)

    def test_invalid_request_status_transition_is_denied_and_does_not_mutate_status(self):
        original = RequestCard(
            request_id="demo-001",
            title="Original title",
            subject="Original subject",
            clean_customer_request="Original clean request",
            internal_notes="Internal note",
            priority=RequestPriority.HIGH,
            source_type=RequestSourceType.EMAIL,
            source_ref="email:demo",
            counterparty_ref="counterparty:demo",
            customer_ref="customer:demo",
            responsible_user_ref="user:manager",
            assistant_user_ref="user:assistant",
        )
        self.repository.create_request(original)
        before = self.repository.get_request("demo-001").value.to_dict()

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.QUOTE_SENT,
            actor_permissions={"quote.send"},
        )
        current = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION)
        self.assertEqual(current.to_dict(), before)

    def test_valid_request_status_transition_mutates_only_status_and_updated_at(self):
        old_timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        original = RequestCard(
            request_id="demo-001",
            title="Original title",
            subject="Original subject",
            clean_customer_request="Original clean request",
            internal_notes="Internal note",
            priority=RequestPriority.HIGH,
            source_type=RequestSourceType.EMAIL,
            source_ref="email:demo",
            counterparty_ref="counterparty:demo",
            customer_ref="customer:demo",
            responsible_user_ref="user:manager",
            assistant_user_ref="user:assistant",
            created_at=old_timestamp,
            updated_at=old_timestamp,
        )
        self.repository.create_request(original)
        before = self.repository.get_request("demo-001").value.to_dict()

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.NEW,
            actor_permissions={"request.change_status"},
        )
        after = result.value.to_dict()

        self.assertTrue(result.success)
        self.assertEqual(after["status"], RequestStatus.NEW.value)
        self.assertNotEqual(after["updated_at"], before["updated_at"])
        for key in before:
            if key not in {"status", "updated_at"}:
                self.assertEqual(after[key], before[key])

    def test_valid_request_status_transition_updates_status(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.NEW,
            actor_permissions={"request.change_status"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.value.status, RequestStatus.NEW)
        self.assertEqual(self.repository.get_request("demo-001").value.status, RequestStatus.NEW)

    def test_direct_update_request_with_changed_status_is_denied_without_mutation(self):
        original = RequestCard(request_id="demo-001", title="Original title", internal_notes="Internal note")
        self.repository.create_request(original)
        changed = replace(original, status=RequestStatus.NEW, title="Updated title")

        result = self.repository.update_request(changed)
        stored = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.INVALID_STATE_TRANSITION)
        self.assertEqual(result.error.details["reason"], "direct_status_update_forbidden")
        self.assertEqual(stored.to_dict(), original.to_dict())

    def test_direct_update_request_without_status_change_updates_non_status_fields(self):
        original = RequestCard(request_id="demo-001", title="Original title", internal_notes="Internal note")
        self.repository.create_request(original)
        changed = replace(original, title="Updated title", internal_notes="Updated internal note")

        result = self.repository.update_request(changed)

        self.assertTrue(result.success)
        self.assertEqual(result.value.status, original.status)
        self.assertEqual(result.value.title, "Updated title")
        self.assertEqual(result.value.internal_notes, "Updated internal note")

    def test_updating_position_status_uses_guard_rules(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.add_position(
            RequestPosition(position_id="pos-001", request_id="demo-001", line_no=1, source_text="Pressure gauge")
        )

        result = self.repository.update_position_status(
            "pos-001",
            RequestPositionStatus.PARSED,
            actor_permissions={"agent.run"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.value.status, RequestPositionStatus.PARSED)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.ALLOWED_TRANSITION)

    def test_direct_update_position_with_changed_status_is_denied_without_mutation(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        original = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            review_reason="Original review reason",
        )
        self.repository.add_position(original)
        changed = replace(original, status=RequestPositionStatus.PARSED, review_reason="Updated review reason")

        result = self.repository.update_position(changed)
        stored = self.repository.get_position("pos-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.INVALID_STATE_TRANSITION)
        self.assertEqual(result.error.details["reason"], "direct_status_update_forbidden")
        self.assertEqual(stored.to_dict(), original.to_dict())

    def test_direct_update_position_without_status_change_updates_non_status_fields(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        original = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            review_reason="Original review reason",
        )
        self.repository.add_position(original)
        changed = replace(original, source_text="Updated source text", review_reason="Updated review reason")

        result = self.repository.update_position(changed)

        self.assertTrue(result.success)
        self.assertEqual(result.value.status, original.status)
        self.assertEqual(result.value.source_text, "Updated source text")
        self.assertEqual(result.value.review_reason, "Updated review reason")

    def test_invalid_position_transition_is_denied_and_does_not_mutate_status(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.add_position(
            RequestPosition(
                position_id="pos-001",
                request_id="demo-001",
                line_no=1,
                source_text="Pressure gauge",
                quantity="2.5",
                unit="pcs",
                parsed_intent_ref="agent_output:demo",
                agent_run_ref="agent_run:demo",
                catalog_item_ref="catalog_item:demo",
                matcher_run_ref="matcher_run:demo",
                needs_review=True,
                review_reason="Original review reason",
            )
        )
        before = self.repository.get_position("pos-001").value.to_dict()

        result = self.repository.update_position_status(
            "pos-001",
            RequestPositionStatus.APPROVED,
            actor_permissions={"request_position.approve"},
        )
        current = self.repository.get_position("pos-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION)
        self.assertEqual(current.to_dict(), before)

    def test_valid_position_status_transition_mutates_only_status_and_updated_at(self):
        old_timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.add_position(
            RequestPosition(
                position_id="pos-001",
                request_id="demo-001",
                line_no=1,
                source_text="Pressure gauge",
                quantity="2.5",
                unit="pcs",
                parsed_intent_ref="agent_output:demo",
                agent_run_ref="agent_run:demo",
                catalog_item_ref="catalog_item:demo",
                matcher_run_ref="matcher_run:demo",
                review_reason="Original review reason",
                created_at=old_timestamp,
                updated_at=old_timestamp,
            )
        )
        before = self.repository.get_position("pos-001").value.to_dict()

        result = self.repository.update_position_status(
            "pos-001",
            RequestPositionStatus.PARSED,
            actor_permissions={"agent.run"},
        )
        after = result.value.to_dict()

        self.assertTrue(result.success)
        self.assertEqual(after["status"], RequestPositionStatus.PARSED.value)
        self.assertNotEqual(after["updated_at"], before["updated_at"])
        for key in before:
            if key not in {"status", "updated_at"}:
                self.assertEqual(after[key], before[key])

    def test_expected_state_mismatch_is_denied_and_does_not_mutate_status(self):
        original = RequestCard(request_id="demo-001", title="Original title", internal_notes="Internal note")
        self.repository.create_request(original)
        before = self.repository.get_request("demo-001").value.to_dict()

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.NEW,
            expected_state=RequestStatus.IN_REVIEW,
            actor_permissions={"request.change_status"},
        )
        current = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_EXPECTED_STATE_MISMATCH)
        self.assertEqual(current.to_dict(), before)

    def test_repository_returns_immutable_safe_objects(self):
        self.repository.create_request(RequestCard(request_id="demo-001", title="Original title"))
        self.repository.add_position(
            RequestPosition(position_id="pos-001", request_id="demo-001", line_no=1, source_text="Pressure gauge")
        )

        stored_request = self.repository.get_request("demo-001").value
        stored_position = self.repository.get_position("pos-001").value

        with self.assertRaises(FrozenInstanceError):
            stored_request.title = "Caller mutation"
        with self.assertRaises(FrozenInstanceError):
            stored_position.source_text = "Caller mutation"

        detached_request = stored_request.with_status(RequestStatus.NEW)
        detached_position = stored_position.with_status(RequestPositionStatus.PARSED)

        self.assertEqual(detached_request.status, RequestStatus.NEW)
        self.assertEqual(detached_position.status, RequestPositionStatus.PARSED)
        self.assertEqual(self.repository.get_request("demo-001").value.status, RequestStatus.DRAFT)
        self.assertEqual(self.repository.get_position("pos-001").value.status, RequestPositionStatus.NEW)

    def test_public_request_serialization_does_not_expose_internal_notes(self):
        card = RequestCard(
            request_id="demo-001",
            internal_notes="Internal margin context must stay hidden.",
            source_ref="email:internal-source",
            responsible_user_ref="user:manager",
        )

        public_payload = card.to_public_dict()

        self.assertNotIn("internal_notes", public_payload)
        self.assertNotIn("source_ref", public_payload)
        self.assertNotIn("responsible_user_ref", public_payload)

    def test_position_public_serialization_hides_processing_refs_and_review_reason(self):
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            parsed_intent_ref="agent_output:demo",
            agent_run_ref="agent_run:demo",
            catalog_item_ref="catalog_item:demo",
            matcher_run_ref="matcher_run:demo",
            review_reason="Internal review detail",
        )

        public_payload = position.to_public_dict()

        self.assertNotIn("parsed_intent_ref", public_payload)
        self.assertNotIn("agent_run_ref", public_payload)
        self.assertNotIn("catalog_item_ref", public_payload)
        self.assertNotIn("matcher_run_ref", public_payload)
        self.assertNotIn("review_reason", public_payload)

    def test_internal_serialization_includes_internal_fields_for_staff_backend_usage(self):
        card = RequestCard(
            request_id="demo-001",
            internal_notes="Internal note",
            source_ref="email:demo",
            responsible_user_ref="user:manager",
        )
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            parsed_intent_ref="agent_output:demo",
            agent_run_ref="agent_run:demo",
            catalog_item_ref="catalog_item:demo",
            matcher_run_ref="matcher_run:demo",
            review_reason="Internal review detail",
        )

        request_payload = card.to_dict()
        position_payload = position.to_dict()

        self.assertEqual(request_payload["internal_notes"], "Internal note")
        self.assertEqual(request_payload["source_ref"], "email:demo")
        self.assertEqual(request_payload["responsible_user_ref"], "user:manager")
        self.assertEqual(position_payload["parsed_intent_ref"], "agent_output:demo")
        self.assertEqual(position_payload["agent_run_ref"], "agent_run:demo")
        self.assertEqual(position_payload["catalog_item_ref"], "catalog_item:demo")
        self.assertEqual(position_payload["matcher_run_ref"], "matcher_run:demo")
        self.assertEqual(position_payload["review_reason"], "Internal review detail")

    def test_serialization_returns_json_friendly_dicts(self):
        card = RequestCard(request_id="demo-001", position_refs=["request_position:pos-001"])
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            quantity="2.5",
        )

        card_payload = card.to_dict()
        position_payload = position.to_dict()

        self.assertIsInstance(card_payload, dict)
        self.assertIsInstance(card.to_public_dict(), dict)
        self.assertIsInstance(card_payload["position_refs"], list)
        self.assertEqual(position_payload["quantity"], "2.5")
        json.dumps(card_payload)
        json.dumps(position_payload)

    def test_json_dumps_works_for_request_public_serialization(self):
        card = RequestCard(request_id="demo-001", title="Demo request", internal_notes="Internal note")

        encoded = json.dumps(card.to_public_dict())

        self.assertIn('"request_id": "demo-001"', encoded)
        self.assertNotIn("Internal note", encoded)

    def test_json_dumps_works_for_position_internal_serialization(self):
        position = RequestPosition(
            position_id="pos-001",
            request_id="demo-001",
            line_no=1,
            source_text="Pressure gauge",
            agent_run_ref="agent_run:demo",
        )

        encoded = json.dumps(position.to_dict())

        self.assertIn('"position_id": "pos-001"', encoded)
        self.assertIn('"agent_run_ref": "agent_run:demo"', encoded)

    def test_repository_test_store_is_isolated_between_tests(self):
        self.assertEqual(self.repository.list_requests(), ())

    def test_missing_request_id_returns_safe_not_found_error(self):
        result = self.repository.get_request("missing")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)
        self.assertEqual(result.error.entity_ref, "request:missing")

    def test_missing_position_id_returns_safe_not_found_error(self):
        result = self.repository.get_position("missing")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)
        self.assertEqual(result.error.entity_ref, "request_position:missing")

    def test_add_position_to_unknown_request_returns_safe_error_without_orphan_position(self):
        position = RequestPosition(
            position_id="pos-001",
            request_id="missing-request",
            line_no=1,
            source_text="Pressure gauge",
        )

        result = self.repository.add_position(position)
        missing_position = self.repository.get_position("pos-001")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)
        self.assertEqual(result.error.entity_ref, "request:missing-request")
        self.assertFalse(missing_position.success)
        self.assertEqual(missing_position.error.code, ErrorCode.NOT_FOUND)

    def test_missing_permission_denies_status_update_without_mutation(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.update_request_status("demo-001", RequestStatus.NEW)
        current = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_MISSING_PERMISSION)
        self.assertEqual(result.error.code, ErrorCode.PERMISSION_DENIED)
        self.assertEqual(current.status, RequestStatus.DRAFT)


if __name__ == "__main__":
    unittest.main()

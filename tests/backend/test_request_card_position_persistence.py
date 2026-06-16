import json
import unittest

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
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.QUOTE_SENT,
            actor_permissions={"quote.send"},
        )
        current = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION)
        self.assertEqual(current.status, RequestStatus.DRAFT)

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

    def test_invalid_position_transition_is_denied_and_does_not_mutate_status(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))
        self.repository.add_position(
            RequestPosition(position_id="pos-001", request_id="demo-001", line_no=1, source_text="Pressure gauge")
        )

        result = self.repository.update_position_status(
            "pos-001",
            RequestPositionStatus.APPROVED,
            actor_permissions={"request_position.approve"},
        )
        current = self.repository.get_position("pos-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION)
        self.assertEqual(current.status, RequestPositionStatus.NEW)

    def test_expected_state_mismatch_is_denied_and_does_not_mutate_status(self):
        self.repository.create_request(RequestCard(request_id="demo-001"))

        result = self.repository.update_request_status(
            "demo-001",
            RequestStatus.NEW,
            expected_state=RequestStatus.IN_REVIEW,
            actor_permissions={"request.change_status"},
        )
        current = self.repository.get_request("demo-001").value

        self.assertFalse(result.success)
        self.assertEqual(result.transition_decision.reason_code, TransitionDecisionReason.DENIED_EXPECTED_STATE_MISMATCH)
        self.assertEqual(current.status, RequestStatus.DRAFT)

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
            matcher_run_ref="matcher_run:demo",
            review_reason="Internal review detail",
        )

        public_payload = position.to_public_dict()

        self.assertNotIn("parsed_intent_ref", public_payload)
        self.assertNotIn("agent_run_ref", public_payload)
        self.assertNotIn("matcher_run_ref", public_payload)
        self.assertNotIn("review_reason", public_payload)

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
        self.assertIsInstance(card_payload["position_refs"], list)
        self.assertEqual(position_payload["quantity"], "2.5")
        json.dumps(card_payload)
        json.dumps(position_payload)

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

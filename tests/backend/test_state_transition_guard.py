import unittest

from backend.app.auth.permissions import ActorContext, ActorType
from backend.app.common import ErrorCode
from backend.app.workflow import (
    StateMachineDefinition,
    StateTransitionGuard,
    TransitionDecisionReason,
    TransitionRequest,
    TransitionRule,
    WorkflowType,
)


class StateTransitionGuardTests(unittest.TestCase):
    def setUp(self):
        self.guard = StateTransitionGuard([self._request_machine()])
        self.staff_actor = ActorContext(actor_type=ActorType.STAFF_USER, actor_id="user:demo-manager")

    def test_allowed_transition_returns_allowed_decision(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="in_progress",
                correlation_id="corr:demo",
                idempotency_key="idem:demo",
            )
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.ALLOWED_TRANSITION)
        self.assertEqual(decision.from_state, "new")
        self.assertEqual(decision.to_state, "in_progress")
        self.assertEqual(decision.correlation_id, "corr:demo")
        self.assertEqual(decision.idempotency_key, "idem:demo")
        self.assertIsNone(decision.error)

    def test_unknown_workflow_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.QUOTE,
                entity_ref="quote:demo",
                current_state="draft",
                target_state="approved",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_WORKFLOW)

    def test_unknown_current_state_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="unknown",
                target_state="in_progress",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_STATE)

    def test_unknown_target_state_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="unknown",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_STATE)

    def test_unknown_transition_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="quote_draft",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_UNKNOWN_TRANSITION)

    def test_terminal_state_cannot_transition_unless_explicitly_allowed(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="sent",
                target_state="archived",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_TERMINAL_STATE)

    def test_terminal_state_can_transition_when_rule_explicitly_allows_it(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="rejected",
                target_state="archived",
            )
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.ALLOWED_TRANSITION)

    def test_expected_state_mismatch_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="in_progress",
                expected_state="draft",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_EXPECTED_STATE_MISMATCH)
        self.assertEqual(decision.error.code, ErrorCode.CONFLICT)

    def test_required_permission_missing_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="waiting_supplier",
                actor_context=self.staff_actor,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_MISSING_PERMISSION)
        self.assertEqual(decision.required_permission, "supplier_quote.create_request")
        self.assertEqual(decision.error.code, ErrorCode.PERMISSION_DENIED)

    def test_required_permission_present_allows_transition(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="waiting_supplier",
                actor_context=self.staff_actor,
                actor_permissions={"supplier_quote.create_request"},
            )
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.required_permission, "supplier_quote.create_request")

    def test_permission_from_actor_context_allows_transition(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            role_template_permissions={"supplier_quote.create_request"},
        )

        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="waiting_supplier",
                actor_context=actor,
            )
        )

        self.assertTrue(decision.allowed)

    def test_required_reason_missing_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="quote_draft",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_MISSING_REASON)

    def test_required_reason_present_allows_transition(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="quote_draft",
                reason="Manager reviewed supplier status.",
            )
        )

        self.assertTrue(decision.allowed)

    def test_required_fields_missing_are_reported(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="quote_draft",
                target_state="approved",
                provided_fields={"quote_lines"},
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_MISSING_REQUIRED_FIELDS)
        self.assertEqual(decision.missing_fields, ("customer_ref",))

    def test_required_fields_present_allow_transition(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="quote_draft",
                target_state="approved",
                provided_fields={"quote_lines", "customer_ref"},
            )
        )

        self.assertTrue(decision.allowed)

    def test_forbidden_actor_type_is_denied(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="archived",
                actor_context=ActorContext(actor_type=ActorType.GUEST),
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_ACTOR_TYPE)

    def test_allowed_actor_type_can_transition(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="approved",
                target_state="sent",
                actor_context=self.staff_actor,
                actor_permissions={"quote.send"},
            )
        )

        self.assertTrue(decision.allowed)

    def test_self_transition_denied_by_default(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="quote_draft",
                target_state="quote_draft",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, TransitionDecisionReason.DENIED_SELF_TRANSITION)

    def test_self_transition_allowed_when_rule_explicitly_permits_it(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="in_progress",
            )
        )

        self.assertTrue(decision.allowed)

    def test_denied_decision_contains_common_api_error(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="new",
                target_state="quote_draft",
            )
        )

        self.assertFalse(decision.allowed)
        self.assertIsNotNone(decision.error)
        self.assertEqual(decision.error.code, ErrorCode.INVALID_STATE_TRANSITION)

    def test_denied_decision_does_not_expose_secrets_or_raw_payloads(self):
        decision = self.guard.decide(
            TransitionRequest(
                workflow_type=WorkflowType.REQUEST,
                entity_ref="request:demo",
                current_state="in_progress",
                target_state="waiting_supplier",
                actor_permissions={"token=demo-secret"},
                reason="password=demo-password",
                provided_fields={"raw_payload", "api_key"},
            )
        )

        self.assertFalse(decision.allowed)
        serialized_error = str(decision.error.to_dict())
        self.assertNotIn("demo-secret", serialized_error)
        self.assertNotIn("demo-password", serialized_error)
        self.assertNotIn("raw_payload", serialized_error)
        self.assertNotIn("api_key", serialized_error)

    @staticmethod
    def _request_machine():
        return StateMachineDefinition(
            workflow_type=WorkflowType.REQUEST,
            known_states={
                "new",
                "in_progress",
                "waiting_supplier",
                "quote_draft",
                "approved",
                "sent",
                "rejected",
                "archived",
            },
            terminal_states={"sent", "rejected", "archived"},
            initial_state="new",
            transition_rules=(
                TransitionRule("new", "in_progress", description="Start request processing."),
                TransitionRule("in_progress", "waiting_supplier", required_permission="supplier_quote.create_request"),
                TransitionRule("in_progress", "quote_draft", requires_reason=True),
                TransitionRule("quote_draft", "approved", required_fields={"quote_lines", "customer_ref"}),
                TransitionRule(
                    "approved",
                    "sent",
                    required_permission="quote.send",
                    allowed_actor_types={ActorType.STAFF_USER},
                ),
                TransitionRule("new", "archived", forbidden_actor_types={ActorType.GUEST}),
                TransitionRule("in_progress", "in_progress", allow_self_transition=True),
                TransitionRule("rejected", "archived"),
            ),
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.app.auth.permissions import (
    ActorContext,
    ActorType,
    FieldAccessRequest,
    FieldMaskingReason,
    FieldVisibility,
    PermissionDecisionReason,
    PermissionDecisionService,
    PermissionRequest,
)


KNOWN_PERMISSIONS = {
    "agent.run",
    "catalog.import",
    "pricing.view_margin",
    "request.edit",
    "request.view_assigned",
}


class PermissionDecisionServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = PermissionDecisionService(known_permissions=KNOWN_PERMISSIONS)

    def test_role_template_permission_allows_action(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            role_template_permissions={"request.view_assigned"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.ALLOWED_BY_ROLE_TEMPLATE)
        self.assertEqual(decision.matched_permission, "request.view_assigned")

    def test_missing_permission_denies_action(self):
        actor = ActorContext(actor_type=ActorType.STAFF_USER)

        decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_MISSING_PERMISSION)

    def test_explicit_grant_adds_permission(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            explicit_grants={"request.view_assigned"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.ALLOWED_BY_EXPLICIT_GRANT)
        self.assertIn("request.view_assigned", self.service.get_effective_permissions(actor))

    def test_explicit_revoke_overrides_role_template_permission(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            role_template_permissions={"request.view_assigned"},
            explicit_revokes={"request.view_assigned"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_EXPLICIT_REVOKE)
        self.assertNotIn("request.view_assigned", self.service.get_effective_permissions(actor))

    def test_explicit_revoke_overrides_explicit_grant(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            explicit_grants={"request.view_assigned"},
            explicit_revokes={"request.view_assigned"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_EXPLICIT_REVOKE)

    def test_unknown_permission_is_denied(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            role_template_permissions={"unknown.permission"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="unknown.permission"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_UNKNOWN_PERMISSION)
        self.assertIsNone(decision.matched_permission)

    def test_unknown_or_anonymous_actor_is_denied(self):
        for actor_type, expected_reason in (
            (ActorType.UNKNOWN, PermissionDecisionReason.DENIED_UNKNOWN_ACTOR),
            (ActorType.ANONYMOUS, PermissionDecisionReason.DENIED_ANONYMOUS_ACTOR),
            ("unexpected_actor_type", PermissionDecisionReason.DENIED_UNKNOWN_ACTOR),
        ):
            with self.subTest(actor_type=actor_type):
                actor = ActorContext(
                    actor_type=actor_type,
                    role_template_permissions={"request.view_assigned"},
                )

                decision = self.service.decide(actor, PermissionRequest(permission="request.view_assigned"))

                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason_code, expected_reason)

    def test_ownership_required_permission_allows_owner(self):
        actor = ActorContext(
            actor_type=ActorType.CUSTOMER_USER,
            role_template_permissions={"request.edit"},
            owned_object_refs={"request:demo-owned"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(
                permission="request.edit",
                target_ref="request:demo-owned",
                ownership_required=True,
            ),
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.ALLOWED_BY_OWNERSHIP)

    def test_owner_without_requested_permission_is_denied(self):
        actor = ActorContext(
            actor_type=ActorType.CUSTOMER_USER,
            owned_object_refs={"request:demo-owned"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(
                permission="request.edit",
                target_ref="request:demo-owned",
                ownership_required=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_MISSING_PERMISSION)

    def test_ownership_required_permission_denies_non_owner_with_permission(self):
        actor = ActorContext(
            actor_type=ActorType.CUSTOMER_USER,
            role_template_permissions={"request.edit"},
            owned_object_refs={"request:other"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(
                permission="request.edit",
                target_ref="request:demo-owned",
                ownership_required=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_OWNERSHIP_REQUIRED)

    def test_explicit_revoke_overrides_permission_and_ownership(self):
        actor = ActorContext(
            actor_type=ActorType.CUSTOMER_USER,
            role_template_permissions={"request.edit"},
            explicit_revokes={"request.edit"},
            owned_object_refs={"request:demo-owned"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(
                permission="request.edit",
                target_ref="request:demo-owned",
                ownership_required=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_EXPLICIT_REVOKE)

    def test_service_actor_allowed_inside_declared_scope(self):
        actor = ActorContext(
            actor_type=ActorType.SERVICE_ACTOR,
            role_template_permissions={"catalog.import"},
            service_scopes={"catalog_import"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(permission="catalog.import", service_scope="catalog_import"),
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.ALLOWED_BY_SERVICE_SCOPE)

    def test_service_actor_denied_outside_declared_scope(self):
        actor = ActorContext(
            actor_type=ActorType.SERVICE_ACTOR,
            role_template_permissions={"catalog.import"},
            service_scopes={"catalog_import"},
        )

        decision = self.service.decide(
            actor,
            PermissionRequest(permission="catalog.import", service_scope="other_scope"),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_SERVICE_SCOPE)

    def test_sensitive_field_visible_when_permission_exists(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            role_template_permissions={"pricing.view_margin"},
        )

        decision = self.service.decide_field_access(
            actor,
            FieldAccessRequest(field_name="margin", required_permission="pricing.view_margin"),
        )

        self.assertEqual(decision.visibility, FieldVisibility.VISIBLE)
        self.assertEqual(decision.reason_code, FieldMaskingReason.VISIBLE_BY_PERMISSION)

    def test_sensitive_field_masked_hidden_or_denied_when_permission_is_missing(self):
        actor = ActorContext(actor_type=ActorType.STAFF_USER)

        for visibility, expected_reason in (
            (FieldVisibility.MASKED, FieldMaskingReason.MASKED_MISSING_PERMISSION),
            (FieldVisibility.HIDDEN, FieldMaskingReason.HIDDEN_MISSING_PERMISSION),
            (FieldVisibility.DENIED, FieldMaskingReason.DENIED_MISSING_PERMISSION),
        ):
            with self.subTest(visibility=visibility):
                decision = self.service.decide_field_access(
                    actor,
                    FieldAccessRequest(
                        field_name="margin",
                        required_permission="pricing.view_margin",
                        missing_permission_visibility=visibility,
                    ),
                )

                self.assertEqual(decision.visibility, visibility)
                self.assertEqual(decision.reason_code, expected_reason)

    def test_frontend_ui_assumptions_do_not_affect_decision(self):
        actor = ActorContext(
            actor_type=ActorType.STAFF_USER,
            frontend_visible_permissions={"pricing.view_margin"},
        )

        decision = self.service.decide(actor, PermissionRequest(permission="pricing.view_margin"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, PermissionDecisionReason.DENIED_MISSING_PERMISSION)

    def test_decision_result_contains_safe_reason_without_sensitive_payload(self):
        actor = ActorContext(actor_type=ActorType.CUSTOMER_USER)
        secret_like_target_ref = "secret-token-or-customer-payload"

        decision = self.service.decide(
            actor,
            PermissionRequest(
                permission="request.edit",
                target_ref=secret_like_target_ref,
                ownership_required=True,
                sensitive=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.masking_required)
        self.assertIsNotNone(decision.safe_explanation)
        self.assertNotIn(secret_like_target_ref, decision.safe_explanation)


if __name__ == "__main__":
    unittest.main()

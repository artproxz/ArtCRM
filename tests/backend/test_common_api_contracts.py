import unittest
from types import MappingProxyType

from backend.app.common import (
    ErrorCode,
    IdempotencyCheckResult,
    IdempotencyHelper,
    IdempotencyKey,
    IdempotencyStatus,
    REDACTED_VALUE,
    ResponseMeta,
    SeverityLevel,
    conflict_error,
    error_response,
    internal_error,
    invalid_state_transition_error,
    not_found_error,
    permission_denied_error,
    success_response,
    validation_error,
)


class CommonApiContractsTests(unittest.TestCase):
    def test_success_response_contains_success_data_no_error_and_meta(self):
        meta = ResponseMeta(correlation_id="corr:demo")

        response = success_response({"ok": True}, meta=meta)

        self.assertTrue(response.success)
        self.assertEqual(response.data, {"ok": True})
        self.assertIsNone(response.error)
        self.assertEqual(response.meta.correlation_id, "corr:demo")

    def test_error_response_contains_error_no_data_and_meta(self):
        error = permission_denied_error(permission="request.edit")
        meta = ResponseMeta(request_id="request:demo")

        response = error_response(error, meta=meta)

        self.assertFalse(response.success)
        self.assertIsNone(response.data)
        self.assertEqual(response.error, error)
        self.assertEqual(response.meta.request_id, "request:demo")

    def test_response_meta_stores_correlation_request_idempotency_and_audit_ids(self):
        meta = ResponseMeta(
            correlation_id="corr:demo",
            request_id="request:demo",
            idempotency_key="idem:demo",
            audit_event_id="audit_event:demo",
        )

        self.assertEqual(meta.correlation_id, "corr:demo")
        self.assertEqual(meta.request_id, "request:demo")
        self.assertEqual(meta.idempotency_key, "idem:demo")
        self.assertEqual(meta.audit_event_id, "audit_event:demo")

    def test_response_meta_stores_masked_hidden_fields_and_warnings_as_tuples(self):
        meta = ResponseMeta(
            masked_fields=["margin", "purchase_price"],
            hidden_fields=["supplier_response"],
            warnings=["partial_data"],
        )

        self.assertEqual(meta.masked_fields, ("margin", "purchase_price"))
        self.assertEqual(meta.hidden_fields, ("supplier_response",))
        self.assertEqual(meta.warnings, ("partial_data",))

    def test_permission_denied_helper_returns_safe_error(self):
        error = permission_denied_error(permission="pricing.view_margin", field="margin")

        self.assertEqual(error.code, ErrorCode.PERMISSION_DENIED)
        self.assertEqual(error.message, "Permission required for this action.")
        self.assertEqual(error.severity, SeverityLevel.HIGH)
        self.assertFalse(error.retryable)
        self.assertEqual(error.field, "margin")
        self.assertEqual(error.details["permission_required"], "pricing.view_margin")

    def test_validation_error_helper_returns_validation_error(self):
        error = validation_error(field="email", details={"reason": "invalid_format"})

        self.assertEqual(error.code, ErrorCode.VALIDATION_ERROR)
        self.assertEqual(error.field, "email")
        self.assertEqual(error.details["reason"], "invalid_format")

    def test_conflict_helper_returns_conflict(self):
        error = conflict_error(entity_ref="quote:demo")

        self.assertEqual(error.code, ErrorCode.CONFLICT)
        self.assertEqual(error.entity_ref, "quote:demo")

    def test_not_found_helper_returns_not_found(self):
        error = not_found_error(entity_ref="request:missing")

        self.assertEqual(error.code, ErrorCode.NOT_FOUND)
        self.assertEqual(error.entity_ref, "request:missing")

    def test_invalid_state_transition_helper_returns_invalid_state_transition(self):
        error = invalid_state_transition_error(
            entity_ref="request:demo",
            from_state="draft",
            to_state="quote_sent",
        )

        self.assertEqual(error.code, ErrorCode.INVALID_STATE_TRANSITION)
        self.assertEqual(error.details["from_state"], "draft")
        self.assertEqual(error.details["to_state"], "quote_sent")

    def test_internal_error_does_not_expose_raw_exception_text_by_default(self):
        exception = RuntimeError("database password leaked in stack")

        error = internal_error(exception=exception)

        self.assertEqual(error.code, ErrorCode.INTERNAL_ERROR)
        self.assertEqual(error.message, "Internal error.")
        self.assertNotIn("database password leaked", str(error.details))
        self.assertEqual(error.details["exception_type"], "RuntimeError")

    def test_safe_error_details_are_copied_frozen_and_sanitized(self):
        details = {
            "safe": "value",
            "token": "demo-token",
            "nested": {"password": "demo-password", "items": [{"secret": "demo-secret"}]},
        }

        error = validation_error(details=details)
        details["safe"] = "mutated"
        details["nested"]["password"] = "mutated-password"

        self.assertIsInstance(error.details, MappingProxyType)
        self.assertEqual(error.details["safe"], "value")
        self.assertEqual(error.details["token"], REDACTED_VALUE)
        self.assertEqual(error.details["nested"]["password"], REDACTED_VALUE)
        self.assertEqual(error.details["nested"]["items"][0]["secret"], REDACTED_VALUE)
        with self.assertRaises(TypeError):
            error.details["safe"] = "blocked"

    def test_idempotency_key_object_stores_key_safely(self):
        key = IdempotencyKey("  demo-key  ")

        self.assertEqual(key.value, "demo-key")

    def test_idempotency_check_result_supports_new(self):
        result = IdempotencyCheckResult(
            status=IdempotencyStatus.NEW,
            idempotency_key=IdempotencyKey("demo-key"),
        )

        self.assertEqual(result.status, IdempotencyStatus.NEW)
        self.assertFalse(result.is_replay)
        self.assertFalse(result.is_conflict)

    def test_idempotency_check_result_supports_replayed(self):
        result = IdempotencyCheckResult(status=IdempotencyStatus.REPLAYED)

        self.assertEqual(result.status, IdempotencyStatus.REPLAYED)
        self.assertTrue(result.is_replay)

    def test_idempotency_check_result_supports_conflict(self):
        result = IdempotencyCheckResult(status=IdempotencyStatus.CONFLICT)

        self.assertEqual(result.status, IdempotencyStatus.CONFLICT)
        self.assertTrue(result.is_conflict)

    def test_idempotency_helper_detects_same_key_same_fingerprint_as_replay(self):
        helper = IdempotencyHelper()

        result = helper.check(
            idempotency_key="demo-key",
            request_fingerprint="hash:abc",
            existing_key="demo-key",
            existing_fingerprint="hash:abc",
        )

        self.assertEqual(result.status, IdempotencyStatus.REPLAYED)

    def test_idempotency_helper_detects_same_key_different_fingerprint_as_conflict(self):
        helper = IdempotencyHelper()

        result = helper.check(
            idempotency_key="demo-key",
            request_fingerprint="hash:abc",
            existing_key="demo-key",
            existing_fingerprint="hash:def",
        )

        self.assertEqual(result.status, IdempotencyStatus.CONFLICT)

    def test_idempotency_helper_detects_missing_key(self):
        helper = IdempotencyHelper()

        result = helper.check(idempotency_key=" ", request_fingerprint="hash:abc")

        self.assertEqual(result.status, IdempotencyStatus.MISSING)


if __name__ == "__main__":
    unittest.main()

"""Common backend API contract helpers for ArtCRM."""

from .api import ApiResponse, ResponseMeta, error_response, success_response
from .errors import (
    ApiError,
    ErrorCode,
    REDACTED_VALUE,
    SeverityLevel,
    conflict_error,
    freeze_safe_details,
    internal_error,
    invalid_state_transition_error,
    not_found_error,
    permission_denied_error,
    validation_error,
)
from .idempotency import IdempotencyCheckResult, IdempotencyHelper, IdempotencyKey, IdempotencyStatus

__all__ = [
    "ApiError",
    "ApiResponse",
    "ErrorCode",
    "IdempotencyCheckResult",
    "IdempotencyHelper",
    "IdempotencyKey",
    "IdempotencyStatus",
    "REDACTED_VALUE",
    "ResponseMeta",
    "SeverityLevel",
    "conflict_error",
    "error_response",
    "freeze_safe_details",
    "internal_error",
    "invalid_state_transition_error",
    "not_found_error",
    "permission_denied_error",
    "success_response",
    "validation_error",
]

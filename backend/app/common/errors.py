from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional


REDACTED_VALUE = "[REDACTED]"

SENSITIVE_DETAIL_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "client_secret",
        "api_key",
        "authorization",
        "cookie",
        "session",
        "private_key",
        "raw_prompt",
        "full_prompt",
        "raw_llm_prompt",
        "raw_llm_response",
        "raw_payload",
        "request_payload",
        "email_body",
        "full_email_body",
        "supplier_confidential_response",
        "full_supplier_confidential_response",
    }
)


class ErrorCode(str, Enum):
    """Stable API error vocabulary for future backend endpoints."""

    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    CONFLICT = "conflict"
    INVALID_STATE_TRANSITION = "invalid_state_transition"
    UNKNOWN_PERMISSION = "unknown_permission"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    DUPLICATE_REQUEST = "duplicate_request"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    INTERNAL_ERROR = "internal_error"


class SeverityLevel(str, Enum):
    """Common severity levels for safe API errors."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def empty_details() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class ApiError:
    """Safe API error object.

    Raw exceptions and raw payloads should be handled by callers outside this
    object. Details are sanitized and frozen to keep response errors stable.
    """

    code: ErrorCode
    message: str
    details: Mapping[str, Any] = field(default_factory=empty_details)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    retryable: bool = False
    field: Optional[str] = None
    entity_ref: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _coerce_error_code(self.code))
        object.__setattr__(self, "severity", _coerce_severity(self.severity))
        object.__setattr__(self, "details", freeze_safe_details(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": thaw_for_json(self.details),
            "severity": self.severity.value,
            "retryable": self.retryable,
            "field": self.field,
            "entity_ref": self.entity_ref,
        }


def permission_denied_error(
    *,
    permission: Optional[str] = None,
    field: Optional[str] = None,
    entity_ref: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
) -> ApiError:
    safe_details = {"permission_required": permission} if permission else {}
    if details:
        safe_details.update(details)
    return ApiError(
        code=ErrorCode.PERMISSION_DENIED,
        message="Permission required for this action.",
        details=safe_details,
        severity=SeverityLevel.HIGH,
        retryable=False,
        field=field,
        entity_ref=entity_ref,
    )


def validation_error(
    *,
    field: Optional[str] = None,
    message: str = "Request validation failed.",
    details: Optional[Mapping[str, Any]] = None,
    entity_ref: Optional[str] = None,
) -> ApiError:
    return ApiError(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        details=details or {},
        severity=SeverityLevel.MEDIUM,
        retryable=False,
        field=field,
        entity_ref=entity_ref,
    )


def conflict_error(
    *,
    message: str = "The request conflicts with the current resource state.",
    details: Optional[Mapping[str, Any]] = None,
    entity_ref: Optional[str] = None,
) -> ApiError:
    return ApiError(
        code=ErrorCode.CONFLICT,
        message=message,
        details=details or {},
        severity=SeverityLevel.MEDIUM,
        retryable=False,
        entity_ref=entity_ref,
    )


def not_found_error(
    *,
    entity_ref: Optional[str] = None,
    message: str = "The requested resource was not found.",
    details: Optional[Mapping[str, Any]] = None,
) -> ApiError:
    return ApiError(
        code=ErrorCode.NOT_FOUND,
        message=message,
        details=details or {},
        severity=SeverityLevel.LOW,
        retryable=False,
        entity_ref=entity_ref,
    )


def invalid_state_transition_error(
    *,
    entity_ref: Optional[str] = None,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
) -> ApiError:
    safe_details = {}
    if from_state is not None:
        safe_details["from_state"] = from_state
    if to_state is not None:
        safe_details["to_state"] = to_state
    if details:
        safe_details.update(details)
    return ApiError(
        code=ErrorCode.INVALID_STATE_TRANSITION,
        message="State transition is not allowed.",
        details=safe_details,
        severity=SeverityLevel.MEDIUM,
        retryable=False,
        entity_ref=entity_ref,
    )


def internal_error(
    *,
    message: str = "Internal error.",
    details: Optional[Mapping[str, Any]] = None,
    exception: Optional[BaseException] = None,
    retryable: bool = False,
) -> ApiError:
    """Build a safe internal error without exposing raw exception text."""

    safe_details = dict(details or {})
    if exception is not None:
        safe_details.setdefault("exception_type", exception.__class__.__name__)
    return ApiError(
        code=ErrorCode.INTERNAL_ERROR,
        message=message,
        details=safe_details,
        severity=SeverityLevel.CRITICAL,
        retryable=retryable,
    )


def freeze_safe_details(details: Mapping[str, Any]) -> Mapping[str, Any]:
    return _deep_freeze(_sanitize_mapping(details))


def thaw_for_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_for_json(inner_value) for key, inner_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_for_json(item) for item in value]
    return value


def _sanitize_mapping(details: Mapping[str, Any]) -> Mapping[str, Any]:
    return {str(key): _sanitize_value(str(key), value) for key, value in details.items()}


def _sanitize_value(key: str, value: Any) -> Any:
    if _is_sensitive_key(key):
        return REDACTED_VALUE
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_sanitize_value("", item) for item in value]
    if isinstance(value, BaseException):
        return value.__class__.__name__
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return normalized in SENSITIVE_DETAIL_KEYS


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(inner_value) for key, inner_value in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _coerce_error_code(code: ErrorCode) -> ErrorCode:
    if isinstance(code, ErrorCode):
        return code
    return ErrorCode(code)


def _coerce_severity(severity: SeverityLevel) -> SeverityLevel:
    if isinstance(severity, SeverityLevel):
        return severity
    return SeverityLevel(severity)

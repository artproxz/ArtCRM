from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from .errors import ApiError, thaw_for_json


def empty_tuple() -> Tuple[str, ...]:
    return ()


@dataclass(frozen=True)
class ResponseMeta:
    """Common response metadata shared by future backend APIs."""

    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    audit_event_id: Optional[str] = None
    masked_fields: Tuple[str, ...] = field(default_factory=empty_tuple)
    hidden_fields: Tuple[str, ...] = field(default_factory=empty_tuple)
    warnings: Tuple[str, ...] = field(default_factory=empty_tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "masked_fields", tuple(self.masked_fields))
        object.__setattr__(self, "hidden_fields", tuple(self.hidden_fields))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "idempotency_key": self.idempotency_key,
            "audit_event_id": self.audit_event_id,
            "masked_fields": thaw_for_json(self.masked_fields),
            "hidden_fields": thaw_for_json(self.hidden_fields),
            "warnings": thaw_for_json(self.warnings),
        }


@dataclass(frozen=True)
class ApiResponse:
    """Common response envelope for future route handlers."""

    success: bool
    data: Any = None
    error: Optional[ApiError] = None
    meta: ResponseMeta = field(default_factory=ResponseMeta)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", ensure_meta(self.meta))

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": thaw_for_json(self.data),
            "error": self.error.to_dict() if self.error else None,
            "meta": self.meta.to_dict(),
        }


def success_response(data: Any, meta: Optional[ResponseMeta] = None) -> ApiResponse:
    return ApiResponse(success=True, data=data, error=None, meta=ensure_meta(meta))


def error_response(error: ApiError, meta: Optional[ResponseMeta] = None) -> ApiResponse:
    return ApiResponse(success=False, data=None, error=error, meta=ensure_meta(meta))


def ensure_meta(meta: Optional[ResponseMeta]) -> ResponseMeta:
    if meta is None:
        return ResponseMeta()
    if isinstance(meta, ResponseMeta):
        return meta
    raise TypeError("meta must be ResponseMeta or None")

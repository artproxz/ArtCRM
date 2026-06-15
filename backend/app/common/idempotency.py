from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IdempotencyStatus(str, Enum):
    """Idempotency check statuses for future mutating APIs."""

    NEW = "new"
    REPLAYED = "replayed"
    CONFLICT = "conflict"
    MISSING = "missing"


@dataclass(frozen=True)
class IdempotencyKey:
    """Safe idempotency key value object."""

    value: str

    def __post_init__(self) -> None:
        normalized = str(self.value).strip()
        if not normalized:
            raise ValueError("idempotency key must not be empty")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class IdempotencyCheckResult:
    """Result of comparing an incoming key/fingerprint to a known record."""

    status: IdempotencyStatus
    idempotency_key: Optional[IdempotencyKey] = None
    incoming_fingerprint: Optional[str] = None
    existing_fingerprint: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdempotencyStatus):
            object.__setattr__(self, "status", IdempotencyStatus(self.status))

    @property
    def is_replay(self) -> bool:
        return self.status == IdempotencyStatus.REPLAYED

    @property
    def is_conflict(self) -> bool:
        return self.status == IdempotencyStatus.CONFLICT


class IdempotencyHelper:
    """Stateless idempotency comparison helper.

    Persistence, distributed locks, request storage, and HTTP middleware are
    intentionally left to future implementation tasks.
    """

    def check(
        self,
        *,
        idempotency_key: Optional[str],
        request_fingerprint: str,
        existing_key: Optional[str] = None,
        existing_fingerprint: Optional[str] = None,
    ) -> IdempotencyCheckResult:
        if idempotency_key is None or not str(idempotency_key).strip():
            return IdempotencyCheckResult(
                status=IdempotencyStatus.MISSING,
                incoming_fingerprint=self._normalize_fingerprint(request_fingerprint),
            )

        key = IdempotencyKey(idempotency_key)
        incoming = self._normalize_fingerprint(request_fingerprint)

        if existing_key is None:
            return IdempotencyCheckResult(
                status=IdempotencyStatus.NEW,
                idempotency_key=key,
                incoming_fingerprint=incoming,
            )

        known_key = IdempotencyKey(existing_key)
        existing = self._normalize_fingerprint(existing_fingerprint)

        if known_key != key:
            return IdempotencyCheckResult(
                status=IdempotencyStatus.NEW,
                idempotency_key=key,
                incoming_fingerprint=incoming,
                existing_fingerprint=existing,
            )

        if existing == incoming:
            return IdempotencyCheckResult(
                status=IdempotencyStatus.REPLAYED,
                idempotency_key=key,
                incoming_fingerprint=incoming,
                existing_fingerprint=existing,
            )

        return IdempotencyCheckResult(
            status=IdempotencyStatus.CONFLICT,
            idempotency_key=key,
            incoming_fingerprint=incoming,
            existing_fingerprint=existing,
        )

    @staticmethod
    def _normalize_fingerprint(fingerprint: Optional[str]) -> str:
        return "" if fingerprint is None else str(fingerprint).strip()

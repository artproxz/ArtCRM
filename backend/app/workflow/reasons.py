from __future__ import annotations

from enum import Enum


class WorkflowType(str, Enum):
    """Generic workflow/process families supported by the guard foundation."""

    REQUEST = "request"
    REQUEST_POSITION = "request_position"
    AGENT_RUN = "agent_run"
    COUNTERPARTY_IMPORT = "counterparty_import"
    COUNTERPARTY_ENRICHMENT = "counterparty_enrichment"
    SUPPLIER_QUOTE = "supplier_quote"
    QUOTE = "quote"
    DOCUMENT = "document"
    PURCHASE = "purchase"
    CUSTOMER_CART = "customer_cart"
    GENERIC = "generic"


class TransitionDecisionReason(str, Enum):
    """Stable reason codes returned by state transition decisions."""

    ALLOWED_TRANSITION = "allowed_transition"
    DENIED_UNKNOWN_WORKFLOW = "denied_unknown_workflow"
    DENIED_UNKNOWN_STATE = "denied_unknown_state"
    DENIED_UNKNOWN_TRANSITION = "denied_unknown_transition"
    DENIED_TERMINAL_STATE = "denied_terminal_state"
    DENIED_EXPECTED_STATE_MISMATCH = "denied_expected_state_mismatch"
    DENIED_MISSING_PERMISSION = "denied_missing_permission"
    DENIED_MISSING_REASON = "denied_missing_reason"
    DENIED_MISSING_REQUIRED_FIELDS = "denied_missing_required_fields"
    DENIED_ACTOR_TYPE = "denied_actor_type"
    DENIED_SELF_TRANSITION = "denied_self_transition"
    DENIED_INVALID_TRANSITION = "denied_invalid_transition"

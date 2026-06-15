# MVP Workflow State Machines And Transition Guards

This document defines implementation-ready conceptual state machines and transition guards for the first backend MVP.

It is documentation only. It does not implement a workflow engine, backend code, API routes, database schema, SQL, ORM, migrations, frontend UI, tests, dependencies, containers, integrations, real data, credentials, tokens, secrets, or business logic.

## Purpose

Staff workspace, SLA, notifications, analytics, quote lifecycle, supplier quote workflow, document visibility, agent review, matcher decisions, counterparty import, and purchase workflows all depend on consistent entity states.

This document converts the current architecture into state machine contracts that future backend services can use for transition validation, permissions, audit events, and UI-safe status presentation.

## Global Transition Guard Rules

- Frontend may request a transition, but backend decides whether it is allowed.
- Every transition must validate current state, target state, actor permission, object ownership, required approvals, and idempotency where applicable.
- Every successful transition must emit an audit event.
- Every denied sensitive transition should emit `permission.denied` or `state_transition.denied` without leaking restricted data.
- Customer-visible status may differ from internal status.
- Service actors can transition only within scoped backend workflows.
- Agent/LLM states are reviewable support states and never final business truth.

## Shared Transition Table Fields

Each state machine below follows the same implementation-readiness dimensions:

- states;
- allowed transitions;
- forbidden transitions;
- initiator;
- required permission;
- audit event;
- SLA effect;
- notification effect;
- customer-visible status effect;
- approval required;
- rollback/reopen/cancel/archive rules.

## 1. RequestCard

Purpose: request-level CRM workflow created from mail, marketplace, manual input, or tender conversion.

States:

- `incoming`
- `parsed`
- `draft`
- `needs_review`
- `ready_for_matching`
- `matched`
- `waiting_supplier`
- `quote_draft`
- `quote_approval`
- `quote_sent`
- `waiting_customer`
- `accepted`
- `rejected`
- `canceled`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `incoming` -> `parsed` | service_actor / agent workflow | `agent.run` or scoped intake permission | `request.parsed` | Starts intake timer | Optional new request notification | Hidden/internal | No |
| `parsed` -> `draft` | backend validation | scoped service permission | `request.created` | Starts request workflow timer | New request queue notification | Hidden/internal or received | No |
| `draft` -> `needs_review` | backend / manager | `request.edit` | `request.state_changed` | May keep active timer | Review required notification | Optional customer status unchanged | No |
| `needs_review` -> `draft` | manager / assistant | `request.edit` | `request.updated` | No reset unless policy says | Assigned user notification | Hidden/internal | No |
| `draft` -> `ready_for_matching` | manager / backend | `request.change_status` | `request.state_changed` | Product selection timer may start | Matcher-ready notification | Hidden/internal | No |
| `ready_for_matching` -> `matched` | Catalog Matcher / manager | `matcher.run` / `matcher.view_result` | `matcher.decision_created` | No direct customer SLA reset | Match result notification | Hidden/internal | Depends on match decision |
| `matched` -> `waiting_supplier` | manager | `supplier_quote.create_request` | `request.state_changed` | Supplier waiting pause may start | Supplier waiting notification | Customer may see in progress | No |
| `matched` -> `quote_draft` | manager | `quote.create_draft` | `quote.created` | Quote preparation timer starts | Quote draft notification | Hidden/internal | No |
| `quote_draft` -> `quote_approval` | manager | `quote.request_approval` | `quote.approval_requested` | Approval timer starts | Approver notification | Hidden/internal | Yes |
| `quote_approval` -> `quote_sent` | approver/manager | `quote.approve` and `quote.send` | `quote.sent` | Waiting customer starts | Customer/internal notification | Customer-facing quote sent | Yes |
| `quote_sent` -> `waiting_customer` | backend / manager | `request.change_status` | `request.state_changed` | Customer waiting pause starts | Follow-up reminder optional | Customer-facing waiting response | No |
| `waiting_customer` -> `accepted` | manager | `request.change_status` | `request.accepted` | Stops active SLA | Outcome notification | Customer-facing accepted | No |
| active state -> `rejected` | manager | `request.change_status` | `request.rejected` | Stops or marks closed | Outcome notification | Customer-facing rejected if safe | May require reason |
| active state -> `canceled` | manager | `request.change_status` | `request.canceled` | Stops active SLA | Cancellation notification | Customer-facing canceled if safe | May require reason |
| terminal state -> `archived` | manager / service_actor | `request.archive` | `request.archived` | No active SLA | Optional archive notification | Hidden/history | No |

Forbidden transitions:

- `incoming` -> `approved` / `quote_sent` / `accepted`.
- `draft` -> `quote_sent` without matching, quote draft, approval rules, and quote version snapshot.
- `waiting_supplier` -> customer-visible price/delivery update without supplier response apply action.
- `archived` -> active state without explicit reopen workflow.

Rollback/reopen/cancel/archive rules:

- Reopen from `rejected`, `canceled`, or `archived` requires `request.change_status` or elevated reopen permission, reason, and audit.
- Archive never deletes audit history.
- Customer-visible status can remain less detailed than internal status.

## 2. RequestPosition

Purpose: one product/service line inside a request.

States:

- `parsed`
- `draft`
- `needs_review`
- `ready_for_matching`
- `matched`
- `approved`
- `rejected`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `parsed` -> `draft` | backend validation | scoped service permission | `request_position.created` | No direct SLA | Request update notification optional | Hidden/internal | No |
| `draft` -> `needs_review` | backend / manager | `request_position.edit` | `request_position.state_changed` | May block matching | Review notification | Hidden/internal | No |
| `needs_review` -> `draft` | manager | `request_position.edit` | `request_position.updated` | No reset | Assigned notification optional | Hidden/internal | No |
| `draft` -> `ready_for_matching` | manager / backend | `request_position.edit` | `request_position.ready_for_matching` | Enables matcher work | Matcher-ready notification | Hidden/internal | No |
| `ready_for_matching` -> `matched` | Catalog Matcher | `matcher.run` | `matcher.decision_created` | No direct SLA | Match result notification | Hidden/internal | Depends on decision |
| `matched` -> `approved` | manager | `request_position.approve` | `request_position.approved` | May unblock quote draft | Position approved notification | May show as selected/confirmed if customer policy allows | Yes |
| active state -> `rejected` | manager | `request_position.edit` | `request_position.rejected` | May block parent request | Review notification | Hidden/internal | Reason required |
| terminal state -> `archived` | manager/service_actor | `request_position.edit` | `request_position.archived` | No active SLA | Optional | Hidden/history | No |

Forbidden transitions:

- `parsed` -> `approved` without draft validation and match/review.
- `needs_review` -> `approved` without corrections.
- `matched` -> quote line if matcher decision is `needs_review`, `no_match`, or `blocked`.

Rollback/reopen/cancel/archive rules:

- Approved positions can be revised only by creating a new review/edit event and invalidating dependent quote drafts if needed.
- Archived positions remain in audit and historical quote links.

## 3. AgentRun

Purpose: auditable execution and review state for LLM/backend-controlled agent workflows.

States:

- `queued`
- `running`
- `completed`
- `failed`
- `needs_review`
- `rejected`
- `approved`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `queued` -> `running` | Agent Orchestrator | `agent.run` scoped | `agent_run.started` | No direct customer SLA | Optional internal | Hidden/internal | No |
| `running` -> `completed` | Agent Orchestrator | scoped service permission | `agent_run.completed` | May unblock validation | Optional | Hidden/internal | No |
| `running` -> `failed` | Agent Orchestrator | scoped service permission | `agent_run.failed` | Must not block entire request by default | Review/fallback notification | Hidden/internal | No |
| `completed` -> `needs_review` | backend validation | scoped service permission | `agent_run.validation_needs_review` | May hold affected position | Manager review notification | Hidden/internal | No |
| `completed` -> `approved` | backend / reviewer | `agent.accept_output` | `agent_output.accepted` | May unblock downstream workflow | Optional | Hidden/internal | Yes for business-impacting output |
| `needs_review` -> `approved` | manager | `agent.accept_output` | `agent_output.accepted` | Unblocks affected workflow | Optional | Hidden/internal | Yes |
| `needs_review` -> `rejected` | manager | `agent.accept_output` | `agent_output.rejected` | Affected data remains reviewable/manual | Optional | Hidden/internal | Yes |
| terminal state -> `archived` | service_actor | scoped retention permission | `agent_run.archived` | None | None | Hidden/internal | No |

Forbidden transitions:

- `completed` -> final business entity without backend validation.
- `failed` -> `approved` without retry/new run/review.
- Any AgentRun state directly calculating prices, VAT, totals, requisites, KP/PDF, or 1C documents.

Rollback/reopen/cancel/archive rules:

- Failed runs can be retried by creating a new AgentRun or controlled retry record.
- Rejected output must remain traceable and not be silently overwritten.
- Archived AgentRuns remain available for quality/audit according to retention policy.

## 4. CatalogMatcherRun

Purpose: backend-only matching decision over validated candidate data and active catalog publication.

States:

- `requested`
- `running`
- `decision_created`
- `needs_review`
- `accepted`
- `rejected`
- `overridden`
- `failed`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `requested` -> `running` | matcher service | `matcher.run` scoped | `matcher.started` | None | None | Hidden/internal | No |
| `running` -> `decision_created` | matcher service | scoped service permission | `matcher.decision_created` | May unblock request position | Manager notification | Hidden/internal | No |
| `decision_created` -> `needs_review` | matcher/backend | scoped service permission | `matcher.needs_review` | May block quote draft | Review notification | Hidden/internal | No |
| `decision_created` -> `accepted` | manager | `matcher.view_result` / position approval | `matcher.decision_accepted` | Unblocks position approval | Optional | Hidden/internal | Yes if decision affects quote |
| `decision_created` -> `rejected` | manager | `matcher.view_result` | `matcher.decision_rejected` | Keeps position unresolved | Optional | Hidden/internal | Yes |
| `decision_created` -> `overridden` | manager | `matcher.override_decision` | `matcher.decision_overridden` | High-risk unblock/block | Override notification | Hidden/internal | Yes |
| `running` -> `failed` | matcher service | scoped service permission | `matcher.failed` | Keeps position reviewable | Failure notification | Hidden/internal | No |
| terminal state -> `archived` | service_actor | scoped retention permission | `matcher.archived` | None | None | Hidden/internal | No |

Forbidden transitions:

- Matcher cannot calculate prices, create quote lines, generate PDF/KP, or call Ollama.
- Product Selector confidence cannot force `accepted`.
- `overridden` requires reason and audit.

Rollback/reopen/cancel/archive rules:

- Override can be superseded by a new matcher run but must not be deleted.
- Accepted decisions can be invalidated if catalog publication changes before quote snapshot.

## 5. SupplierQuoteRequest

Purpose: controlled request to supplier for price, availability, delivery, service-position feasibility, or clarification.

States:

- `draft`
- `ready_to_send`
- `sent`
- `waiting_response`
- `response_received`
- `partially_answered`
- `applied`
- `canceled`
- `expired`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft` -> `ready_to_send` | manager | `supplier_quote.create_request` | `supplier_quote_request.ready_to_send` | Supplier waiting not started yet | Optional review notification | Hidden/internal | May require review |
| `ready_to_send` -> `sent` | manager/service_actor | `supplier_quote.send_request` | `supplier_quote_request.sent` | Supplier waiting starts | Supplier waiting notification | Customer may see in progress | Yes if policy requires |
| `sent` -> `waiting_response` | backend | scoped service permission | `supplier_quote_request.state_changed` | Supplier waiting active | Reminder/SLA scheduled | Customer may see in progress | No |
| `waiting_response` -> `response_received` | manager/service_actor | `supplier_quote.view_response` | `supplier_quote_response.received` | Supplier waiting may pause/end | Response notification | Hidden/internal | No |
| `response_received` -> `partially_answered` | manager | `supplier_quote.view_response` | `supplier_quote_request.partially_answered` | May keep supplier SLA open | Follow-up notification | Hidden/internal | No |
| `response_received` -> `applied` | manager | `supplier_quote.apply_update` | `supplier_quote_response.update_applied` | May unblock quote draft | Update applied notification | Customer status still controlled by quote/request | Yes |
| active state -> `canceled` | manager | `supplier_quote.create_request` or elevated | `supplier_quote_request.canceled` | Ends supplier wait | Cancellation notification | Hidden/internal | Reason required |
| active state -> `expired` | system_job | scoped SLA permission | `supplier_quote_request.expired` | Marks overdue/expired | SLA notification | Hidden/internal | No |
| terminal state -> `archived` | service_actor | scoped retention permission | `supplier_quote_request.archived` | None | None | Hidden/internal | No |

Forbidden transitions:

- `draft` -> `applied`.
- `sent` supplier request cannot be edited silently; create revision or correction event.
- Supplier quote request must not update customer-facing quote data without response apply and quote/version workflow.

Rollback/reopen/cancel/archive rules:

- Canceled/expired supplier requests can be duplicated into a new draft; original remains audited.
- Reopen requires reason and permission.

## 6. SupplierQuoteResponse

Purpose: supplier answer record that can support internal price/delivery/availability/service updates after review.

States:

- `received`
- `registered`
- `needs_review`
- `partially_validated`
- `validated`
- `applied`
- `rejected`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `received` -> `registered` | manager/service_actor | `supplier_quote.view_response` | `supplier_quote_response.registered` | May end waiting response timer | Response registered notification | Hidden/internal | No |
| `registered` -> `needs_review` | backend/manager | `supplier_quote.view_response` | `supplier_quote_response.needs_review` | May keep request blocked | Review notification | Hidden/internal | No |
| `registered` -> `partially_validated` | manager/backend | `supplier_quote.view_response` | `supplier_quote_response.partially_validated` | Partial unblock possible | Optional | Hidden/internal | Yes for application |
| `partially_validated` -> `validated` | manager | `supplier_quote.view_response` | `supplier_quote_response.validated` | Unblocks apply action | Optional | Hidden/internal | Yes |
| `validated` -> `applied` | manager | `supplier_quote.apply_update` | `supplier_quote_response.update_applied` | May unblock quote draft | Applied notification | Not directly customer-visible | Yes |
| active state -> `rejected` | manager | `supplier_quote.view_response` | `supplier_quote_response.rejected` | Keeps/returns to manual review | Rejection notification | Hidden/internal | Reason required |
| terminal state -> `archived` | service_actor | scoped retention permission | `supplier_quote_response.archived` | None | None | Hidden/internal | No |

Forbidden transitions:

- Supplier response cannot silently update quote/customer-visible data.
- `received` -> `applied` without registration, validation, permission, and audit.
- Rejected response cannot be used for price/delivery snapshots.

Rollback/reopen/cancel/archive rules:

- Applied values can be superseded by new response/application events, not edited silently.
- Rejected/archived responses remain traceable.

## 7. Quote

Purpose: commercial offer lifecycle, separate from request/cart/supplier quote.

States:

- `draft`
- `internal_review`
- `awaiting_approval`
- `approved`
- `sent`
- `accepted`
- `rejected`
- `expired`
- `canceled`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft` -> `internal_review` | manager | `quote.edit` | `quote.state_changed` | Review timer optional | Review notification | Hidden/internal | No |
| `internal_review` -> `awaiting_approval` | manager/backend | `quote.request_approval` | `quote.approval_requested` | Approval timer starts | Approver notification | Hidden/internal | Yes |
| `awaiting_approval` -> `approved` | approver | `quote.approve` | `quote.approved` | May stop approval SLA | Approval notification | Hidden/internal | Yes |
| `awaiting_approval` -> `draft` | approver | `quote.approve` | `quote.revision_requested` | Keeps quote active | Revision notification | Hidden/internal | Yes |
| `approved` -> `sent` | manager/service_actor | `quote.send` | `quote.sent` | Waiting customer starts | Customer/send notification | Customer-visible sent | Yes |
| `sent` -> `accepted` | manager | `request.change_status` or `quote.edit` | `quote.accepted` | Stops quote/customer wait | Outcome notification | Customer-visible accepted | No |
| `sent` -> `rejected` | manager | `request.change_status` or `quote.edit` | `quote.rejected` | Stops quote/customer wait | Outcome notification | Customer-visible rejected | No |
| `sent` -> `expired` | system_job/manager | scoped SLA or `quote.edit` | `quote.expired` | Stops/marks expiry | Expiry notification | Customer-visible expired | No |
| active state -> `canceled` | manager | `quote.edit` | `quote.canceled` | Stops active timers | Cancellation notification | Customer-visible if sent | Reason required |
| terminal state -> `archived` | service_actor | scoped retention permission | `quote.archived` | None | None | History only | No |

Forbidden transitions:

- `draft` -> `sent` without approval/send guards.
- `sent` quote cannot be mutated in place; revise through a new QuoteVersion.
- Quote must not expose purchase price, supplier discount, margin, or supplier response to customer.

Rollback/reopen/cancel/archive rules:

- Sent quote changes require new version/revision.
- Canceled/expired quote can be cloned into a new draft if policy allows.
- Archived quote remains audit-visible.

## 8. QuoteVersion

Purpose: reproducible commercial offer snapshot.

States:

- `draft_snapshot`
- `review_snapshot`
- `approved_snapshot`
- `sent_snapshot`
- `superseded`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft_snapshot` -> `review_snapshot` | manager | `quote.edit` | `quote_version.review_snapshot_created` | Optional | Review notification | Hidden/internal | No |
| `review_snapshot` -> `approved_snapshot` | approver | `quote.approve` | `quote_version.approved_snapshot_created` | Approval completes | Approval notification | Hidden/internal | Yes |
| `approved_snapshot` -> `sent_snapshot` | manager/service_actor | `quote.send` | `quote_version.sent_snapshot_created` | Customer wait starts | Customer/send notification | Customer-visible | Yes |
| `sent_snapshot` -> `superseded` | manager/backend | `quote.edit` / `quote.send` | `quote_version.superseded` | New version controls timers | Revision notification | Old version remains visible/history by policy | Yes if sent |
| terminal state -> `archived` | service_actor | retention permission | `quote_version.archived` | None | None | History only | No |

Forbidden transitions:

- Direct mutation of `sent_snapshot` commercial values.
- Publishing a draft snapshot to customer.

Rollback/reopen/cancel/archive rules:

- Superseded sent versions are retained for reproducibility.
- Customer-facing exports must reference exact `quote_version`.

## 9. Document

Purpose: controlled document metadata and visibility lifecycle.

States:

- `draft`
- `internal_only`
- `pending_publication`
- `customer_visible`
- `unpublished`
- `restricted`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft` -> `internal_only` | manager/service_actor | `documents.create_metadata` | `document.created` | None | Optional | Hidden/internal | No |
| `internal_only` -> `pending_publication` | manager | `documents.publish_customer_visible` | `document.publication_requested` | Optional | Approver notification | Hidden/internal | Yes if policy requires |
| `pending_publication` -> `customer_visible` | approver/manager | `documents.publish_customer_visible` | `document.published_customer_visible` | May unblock customer workflow | Customer/internal notification | Customer-visible | Yes |
| `customer_visible` -> `unpublished` | manager/approver | `documents.publish_customer_visible` | `document.unpublished_customer_visible` | Optional | Customer/internal notification | Hidden from customer after unpublish | Yes |
| any active state -> `restricted` | administrator/director | `documents.view_internal` / elevated | `document.restricted` | Optional | Security notification | Hidden unless permission | Yes |
| terminal state -> `archived` | service_actor/manager | document archive permission | `document.archived` | None | Optional | History only | No |

Forbidden transitions:

- Chat attachment -> `customer_visible` automatically.
- Internal or supplier response document becoming customer-visible without explicit publish event.

Rollback/reopen/cancel/archive rules:

- Unpublish preserves previous publication audit.
- Archived document metadata remains traceable.

## 10. DocumentVersion

Purpose: immutable-ish file/version record under a Document.

States:

- `uploaded`
- `scan_pending`
- `validated`
- `rejected`
- `published`
- `superseded`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `uploaded` -> `scan_pending` | document service | scoped service permission | `document_version.uploaded` | None | Optional | Hidden/internal | No |
| `scan_pending` -> `validated` | document service/manager | scoped or `documents.create_metadata` | `document_version.validated` | None | Optional | Hidden/internal | No |
| `scan_pending` -> `rejected` | document service/manager | scoped or document permission | `document_version.rejected` | May block document publication | Rejection notification | Hidden/internal | No |
| `validated` -> `published` | document service/manager | `documents.publish_customer_visible` | `document_version.published` | Optional | Publication notification | Customer-visible via parent Document | Yes |
| `published` -> `superseded` | document service/manager | `documents.publish_customer_visible` | `document_version.superseded` | Optional | Revision notification | Old version visibility by policy | Yes if customer-visible |
| terminal state -> `archived` | service_actor | retention permission | `document_version.archived` | None | None | History only | No |

Forbidden transitions:

- `uploaded` -> `published` without validation/publication.
- Rejected version cannot be downloaded by customer.

Rollback/reopen/cancel/archive rules:

- Superseded versions remain audit-visible.
- Storage deletion policy is deferred; state machine must not imply physical deletion.

## 11. TenderCandidate

Purpose: candidate tender metadata and relevance classification from Tender Reader/backend rules/manager review.

States:

- `incoming`
- `parsed`
- `needs_review`
- `kept`
- `skipped`
- `blocked_irrelevant`
- `converted_to_request`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `incoming` -> `parsed` | Tender Reader/backend | `agent.run` scoped | `tender.parsed` | Tender deadline timer may start | Tender notification optional | Hidden/internal | No |
| `parsed` -> `needs_review` | backend/rules | scoped service permission | `tender.needs_review` | Deadline risk may start | Manager review notification | Hidden/internal | No |
| `parsed`/`needs_review` -> `kept` | manager | `tender.classify` | `tender.kept` | Active tender workflow starts | Kept notification | Hidden/internal | Yes |
| `parsed`/`needs_review` -> `skipped` | manager | `tender.classify` | `tender.skipped` | Stops tender SLA | Optional | Hidden/internal | Yes |
| `parsed`/`needs_review` -> `blocked_irrelevant` | backend/manager | `tender.classify` | `tender.blocked_irrelevant` | Stops tender SLA | Optional | Hidden/internal | May be backend rule |
| `kept` -> `converted_to_request` | manager | `request.create` | `tender.converted_to_request` | Request SLA starts | New request notification | Hidden/internal | Yes |
| terminal state -> `archived` | service_actor | retention permission | `tender.archived` | None | None | Hidden/history | No |

Forbidden transitions:

- Tender Reader cannot own final keep/skip decision.
- Tender candidate cannot generate KP/PDF/bid/pricing directly.
- Scraping/downloading/submission requires separate architecture.

Rollback/reopen/cancel/archive rules:

- Skipped/blocked tender can be reopened only by permissioned manager with reason.
- Converted tender links to created request and remains audit-visible.

## 12. CounterpartyImport

Purpose: future-ready import flow for counterparties from amoCRM or other controlled sources.

States:

- `uploaded`
- `previewed`
- `validated`
- `needs_review`
- `applied`
- `partially_applied`
- `failed`
- `canceled`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `uploaded` -> `previewed` | service_actor/manager | `counterparty.import_preview` | `counterparty_import.previewed` | None | Import preview notification | Hidden/internal | No |
| `previewed` -> `validated` | backend/manager | `counterparty.import_preview` | `counterparty_import.validated` | None | Optional | Hidden/internal | No |
| `previewed`/`validated` -> `needs_review` | backend/manager | `counterparty.import_preview` | `counterparty_import.needs_review` | None | Review notification | Hidden/internal | No |
| `validated` -> `applied` | manager/service_actor | `counterparty.import_apply` | `counterparty_import.applied` | None | Applied notification | Hidden/internal | Yes |
| `validated`/`needs_review` -> `partially_applied` | manager/service_actor | `counterparty.import_apply` | `counterparty_import.partially_applied` | None | Partial apply notification | Hidden/internal | Yes |
| active state -> `failed` | backend/service_actor | scoped service permission | `counterparty_import.failed` | None | Failure notification | Hidden/internal | No |
| active state -> `canceled` | manager | `counterparty.import_preview` | `counterparty_import.canceled` | None | Optional | Hidden/internal | Reason required |
| terminal state -> `archived` | service_actor | retention permission | `counterparty_import.archived` | None | None | Hidden/history | No |

Forbidden transitions:

- `uploaded` -> `applied` without preview and validation.
- Import must not overwrite duplicate counterparties silently.
- Real external credentials or raw source secrets must not be stored in events or docs.

Rollback/reopen/cancel/archive rules:

- Applied imports need corrective follow-up events rather than silent reversal.
- Partial apply records must identify safe counts and failed reasons.

## 13. Counterparty

Purpose: future customer/counterparty registry entity used by CRM requests, quotes, purchases, and imports.

States:

- `draft_candidate`
- `active`
- `needs_merge_review`
- `merged`
- `suspended`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft_candidate` -> `active` | manager/backend | `counterparty.import_apply` or `counterparty.update` | `counterparty.created` | May unblock request | Optional | Not directly customer-visible | Yes if imported |
| `active` -> `needs_merge_review` | backend/manager | `counterparty.merge_review` | `counterparty.merge_candidate_reviewed` | None | Review notification | Hidden/internal | No |
| `needs_merge_review` -> `merged` | manager | `counterparty.merge_review` | `counterparty.merged` | May update linked entities | Merge notification | Hidden/internal | Yes |
| `active` -> `suspended` | manager/admin | `counterparty.update` | `counterparty.suspended` | May block new requests | Notification optional | Hidden/internal | Yes |
| `active`/`suspended` -> `archived` | manager/admin | `counterparty.update` | `counterparty.archived` | None | Optional | Hidden/history | Yes |

Forbidden transitions:

- Duplicate merge must not be automatic without review.
- Counterparty export requires `counterparty.export` and audit.
- Customer organization sharing is not implied by counterparty status.

Rollback/reopen/cancel/archive rules:

- Merge should preserve source refs and alias history.
- Archived counterparties can be restored only by elevated permission and audit.

## 14. CounterpartyEnrichment

Purpose: future reviewable application of external/enriched counterparty data.

States:

- `requested`
- `previewed`
- `validated`
- `needs_review`
- `applied`
- `rejected`
- `failed`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `requested` -> `previewed` | service_actor | `counterparty.enrichment_request` | `counterparty_enrichment.previewed` | None | Optional | Hidden/internal | No |
| `previewed` -> `validated` | backend | scoped validation/service permission or `counterparty.enrichment_request` | `counterparty_enrichment.validated` | None | Optional | Hidden/internal | No |
| `previewed`/`validated` -> `needs_review` | backend/manager | `counterparty.enrichment_request` | `counterparty_enrichment.needs_review` | None | Review notification | Hidden/internal | No |
| `validated`/`needs_review` -> `applied` | manager | `counterparty.enrichment_apply` | `counterparty_enrichment.applied` | None | Applied notification | Hidden/internal | Yes |
| active state -> `rejected` | manager | `counterparty.enrichment_apply` | `counterparty_enrichment.rejected` | None | Optional | Hidden/internal | Reason required |
| active state -> `failed` | service_actor | scoped service permission | `counterparty_enrichment.failed` | None | Failure notification | Hidden/internal | No |
| terminal state -> `archived` | service_actor | retention permission | `counterparty_enrichment.archived` | None | None | Hidden/history | No |

Forbidden transitions:

- Enrichment preview/request cannot mutate active counterparty fields.
- Enrichment cannot overwrite active counterparty fields silently.
- Enrichment cannot create purchases or quotes.

Rollback/reopen/cancel/archive rules:

- Applied enrichment can be corrected by new update events.
- Rejected enrichment remains quality signal for source/provider.

## 15. Purchase

Purpose: future procurement/purchase workflow, separate from quote, request, and supplier quote.

States:

- `draft`
- `internal_review`
- `approved`
- `ordered`
- `partially_received`
- `received`
- `canceled`
- `archived`

Allowed transitions:

| From -> To | Initiator | Required permission | Audit event | SLA effect | Notification effect | Customer-visible status | Approval required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `draft` -> `internal_review` | manager | `purchase.create` / `purchase.update` | `purchase.created` or `purchase.state_changed` | None | Review notification | Hidden/internal | No |
| `internal_review` -> `approved` | approver | `purchase.approve` | `purchase.approved` | None | Approval notification | Hidden/internal | Yes |
| `approved` -> `ordered` | manager/service_actor | `purchase.update` | `purchase.ordered` | Procurement timer may start | Ordered notification | Hidden/internal | Yes if policy requires |
| `ordered` -> `partially_received` | manager/service_actor | `purchase.update` | `purchase.partially_received` | May update procurement status | Notification optional | Hidden/internal | No |
| `partially_received` -> `received` | manager/service_actor | `purchase.update` | `purchase.received` | Procurement timer ends | Received notification | Hidden/internal | No |
| active state -> `canceled` | manager/approver | `purchase.update` | `purchase.canceled` | Stops procurement timer | Cancellation notification | Hidden/internal | Reason required |
| terminal state -> `archived` | service_actor | retention permission | `purchase.archived` | None | None | Hidden/history | No |

Forbidden transitions:

- Purchase must not be confused with quote, request, or supplier quote.
- Supplier quote response can support purchase context later but cannot create a confirmed purchase silently.
- Purchase creation/update/approval is commercial-sensitive and auditable.

Rollback/reopen/cancel/archive rules:

- Ordered/received states should be corrected by adjustment events, not silent mutation.
- Canceled purchases can be cloned into a new draft if policy allows.

## Critical Cross-Entity Rules

- Sent quote is immutable or revised through a new `QuoteVersion`.
- Supplier response cannot silently update request, quote, customer-visible data, or purchase data.
- Customer-visible document publication is explicit and audited.
- LLM/AgentRun states are reviewable and never final business truth.
- Request/customer-facing status may differ from internal status.
- Counterparty import supports preview -> validated -> applied / failed / partially_applied.
- Duplicate counterparty merge is manual/reviewable.
- Counterparty enrichment preview/request does not mutate the registry; only `counterparty.enrichment_apply` can apply reviewed enrichment fields.
- Purchase is separate from quote/request/supplier quote.
- Backend owns transition guards; frontend never owns final state authority.

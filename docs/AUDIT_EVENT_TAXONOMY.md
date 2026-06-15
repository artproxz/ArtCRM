# Audit Event Taxonomy And Event Model Implementation Readiness

This document defines the unified ArtCRM audit/event taxonomy before backend implementation.

It is documentation only. It does not implement event storage, database schema, SQL, ORM, migrations, API routes, backend services, analytics backend, dependencies, containers, real data, credentials, tokens, secrets, or business logic.

## Purpose

Audit events are the shared foundation for:

- RBAC and permission enforcement;
- permission grant/revoke tracking;
- denied access analysis;
- manager workflow history;
- request and quote lifecycle traceability;
- supplier response application;
- customer-visible document publication;
- notifications, reminders, and SLA alerts;
- analytics dashboards;
- agent validation and quality reports;
- matcher decision review;
- counterparty import/enrichment quality;
- future integrations and 1C handoff traceability.

The event model must be stable before backend implementation so security, analytics, and workflow code do not diverge.

## Core Rules

- Audit events are append-oriented and must not be silently rewritten.
- Events must not contain secrets, credentials, raw tokens, private keys, full prompts, or unrestricted raw customer data.
- Event metadata should contain references and safe summaries, not sensitive payload dumps.
- Sensitive events must set `sensitive_flag=true` and define a `redaction_policy`.
- Permission checks must emit audit events for sensitive grant, revoke, denial, and use cases.
- Agent output and matcher decisions must be traceable through AgentRun, matcher run, request position, and reviewer decision references.

## Audit Event Envelope

| Field | Required | Meaning | Notes |
| --- | --- | --- | --- |
| `event_id` | Yes | Stable event identifier. | Unique, immutable. |
| `event_type` | Yes | Normalized event type. | Suggested pattern: `<entity_family>.<action>`. |
| `actor_type` | Yes | Actor category. | See actor types below. |
| `actor_id` | Conditional | Actor reference. | May be null for anonymous guest events if policy allows. |
| `actor_display_name` | Optional | Safe display label. | Must not be used as authorization source. |
| `entity_type` | Yes | Primary entity family. | Example: `quote`, `document`, `matcher_run`. |
| `entity_id` | Conditional | Primary entity reference. | Required when an entity exists. |
| `parent_entity_type` | Optional | Parent context. | Example: quote version under quote, position under request. |
| `parent_entity_id` | Optional | Parent entity reference. | Keeps entity-linked chat/document context. |
| `previous_state` | Optional | State before transition. | Used for state transitions and changes. |
| `new_state` | Optional | State after transition. | Used for state transitions and changes. |
| `permission_used` | Conditional | Permission that allowed action. | Required for sensitive actions and access decisions. |
| `source_service` | Optional | Backend service emitting event. | Example: `catalog_matcher`, `quote_service`. |
| `source_agent_run` | Optional | AgentRun reference. | Required when action consumes LLM candidate data. |
| `idempotency_key` | Optional | Mutating action dedupe key. | Required for mutating APIs where duplicates matter. |
| `timestamp` | Yes | Event time in ISO-8601. | Backend-generated. |
| `metadata` | Optional | Safe structured details. | Must follow redaction policy. |
| `sensitive_flag` | Yes | Whether event is sensitive. | Boolean. |
| `redaction_policy` | Yes | How event is shown/masked. | Example: `public_safe`, `staff_safe`, `commercial_sensitive`, `security_sensitive`. |
| `request_id` | Optional | API request/correlation ID. | Helps trace request chain. |
| `ip_address_hash` | Optional | Hashed network origin. | Store hash, not raw IP, unless future policy allows raw. |
| `user_agent_hash` | Optional | Hashed user-agent. | Store hash or safe fingerprint only. |

Example envelope with placeholder values only:

```json
{
  "event_id": "audit_event:demo-001",
  "event_type": "quote.sent",
  "actor_type": "staff_user",
  "actor_id": "user:demo-manager",
  "actor_display_name": "Demo Manager",
  "entity_type": "quote",
  "entity_id": "quote:demo-001",
  "parent_entity_type": "request",
  "parent_entity_id": "request:demo-001",
  "previous_state": "approved",
  "new_state": "sent",
  "permission_used": "quote.send",
  "source_service": "quote_service",
  "source_agent_run": null,
  "idempotency_key": "demo-idempotency-key",
  "timestamp": "2026-06-12T00:00:00Z",
  "metadata": {
    "quote_version_ref": "quote_version:demo-001-v1",
    "customer_visible_snapshot": true
  },
  "sensitive_flag": true,
  "redaction_policy": "commercial_sensitive",
  "request_id": "request:demo-api-correlation",
  "ip_address_hash": "demo-ip-hash",
  "user_agent_hash": "demo-user-agent-hash"
}
```

## Actor Types

| Actor type | Meaning | Notes |
| --- | --- | --- |
| `staff_user` | Internal CRM employee. | Manager, assistant, director, administrator, future staff. |
| `customer_user` | Authenticated customer. | MVP own-only access. |
| `guest` | Unauthenticated visitor. | Public catalog only; no persistent customer data. |
| `service_actor` | Backend service identity. | Import runner, matcher, generator, integration service. |
| `agent` | LLM agent execution actor. | Always linked to backend-controlled AgentRun. |
| `system_job` | Scheduler/background job. | SLA, reminders, notifications, imports, cleanup. |

Actor rules:

- Human display name is not authorization.
- Service actors require explicit scoped permissions.
- Agent actor events must link to AgentRun and backend validation status.
- Guest events must not create customer-owned business objects before authentication.

## Entity Families

| Entity family | Examples and notes |
| --- | --- |
| `request` | RequestCard lifecycle, assignment, status, archive. |
| `request_position` | Position draft, validation, matcher readiness, approval. |
| `agent_run` | Agent execution, validation, review, quality feedback. |
| `catalog_item` | Catalog read, private field access, publication references. |
| `catalog_publication` | Import/publish/rollback context. |
| `stock_snapshot` | Stock import, publish, freshness. |
| `price_snapshot` | Price source, customer price, purchase price, discounts. |
| `matcher_run` | Catalog Matcher execution and decision records. |
| `supplier_quote_request` | Draft, send, waiting response, cancel. |
| `supplier_quote_response` | Register, validate, apply price/delivery/availability. |
| `quote` | Commercial offer lifecycle. |
| `quote_version` | Customer-facing snapshots and immutable sent versions. |
| `document` | Document metadata, visibility, publication. |
| `document_version` | Upload, validation, download, publish. |
| `message` | Internal Communication Center messages. |
| `notification` | Notification delivery/read/dismiss events. |
| `reminder` | Reminder creation, snooze, complete, cancel. |
| `tender_candidate` | Tender Reader candidate classification and manager decision. |
| `permission` | Grant, revoke, deny, sensitive use. |
| `customer` | Customer profile and own-only/customer support access. |
| `customer_organization` | Future org account, membership, invitation, shared access. |
| `counterparty` | Counterparty search, profile update, export, merge review. |
| `counterparty_import` | Import preview, validation, apply, partial apply, failure. |
| `counterparty_enrichment` | Enrichment request, preview, validation, apply/reject. |
| `purchase` | Purchase draft, update, approval, order/receive lifecycle. |

## Event Categories

| Category | Example event types | Required notes |
| --- | --- | --- |
| read/view | `quote.viewed`, `pricing.purchase_price_viewed`, `counterparty.viewed` | Sensitive reads may require audit even if no state changes. |
| create | `request.created`, `quote.created`, `purchase.created` | Include source service and idempotency key when mutating. |
| update | `request.updated`, `counterparty.updated`, `quote_line.updated` | Include changed safe field names, not full sensitive payloads. |
| delete/archive | `request.archived`, `document.archived`, `message.deleted` | Prefer archive over destructive delete for business entities. |
| restore | `request.restored`, `document.restored` | Requires elevated permission and reason. |
| state_transition | `quote.state_changed`, `supplier_quote_request.state_changed` | Include previous and new state. |
| permission_grant | `permission.granted` | Sensitive; include granted permission and target actor. |
| permission_revoke | `permission.revoked` | Sensitive; include revoked permission and target actor. |
| permission_denied | `permission.denied` | Do not include restricted content in metadata. |
| sensitive_field_viewed | `pricing.margin_viewed`, `pricing.purchase_price_viewed` | Sensitive; include field family and entity reference. |
| export | `quote.exported`, `audit.exported`, `counterparty.exported` | High-risk; include format and scope, not raw export data. |
| publish_customer_visible | `document.published_customer_visible` | Must be explicit and auditable. |
| unpublish_customer_visible | `document.unpublished_customer_visible` | Must preserve prior publication history. |
| agent_run_started | `agent_run.started` | Link to agent name/version and controlled input reference. |
| agent_run_completed | `agent_run.completed` | Does not mean business approval. |
| agent_run_failed | `agent_run.failed` | Error summary must be redacted. |
| agent_output_accepted | `agent_output.accepted` | High-risk when output affects business workflow. |
| matcher_decision_created | `matcher.decision_created` | Link to matcher run and request position. |
| matcher_decision_overridden | `matcher.decision_overridden` | High-risk; require reason and permission. |
| supplier_update_applied | `supplier_quote_response.update_applied` | Must not silently update customer-visible data. |
| quote_sent | `quote.sent` | Customer-facing snapshot becomes visible/sent. |
| quote_approved | `quote.approved` | Approval actor and permission required. |
| document_downloaded | `document.downloaded` | Required for internal/commercial-sensitive docs. |
| counterparty_import_previewed | `counterparty_import.previewed` | Preview does not mutate registry. |
| counterparty_import_applied | `counterparty_import.applied` | High-risk registry mutation. |
| counterparty_merge_candidate_reviewed | `counterparty.merge_candidate_reviewed` | Duplicate merges must be manual/reviewable. |
| purchase_created | `purchase.created` | Purchase is separate from quote/request/supplier quote. |

## High-Risk Event Examples

| Event | Why high risk | Required permission | Sensitive | Suggested metadata |
| --- | --- | --- | --- | --- |
| `pricing.margin_viewed` | Exposes margin. | `pricing.view_margin` | Yes | Entity ref, field family, masking status. |
| `pricing.supplier_discount_viewed` | Exposes supplier discount. | `pricing.view_supplier_discount` | Yes | Quote/item/supplier context. |
| `pricing.purchase_price_viewed` | Exposes purchase price. | `pricing.view_purchase_price` | Yes | Catalog/quote line reference. |
| `document.published_customer_visible` | Internal file can become customer-visible. | `documents.publish_customer_visible` | Yes | Document ref, version ref, prior visibility. |
| `supplier_quote_response.update_applied` | Supplier data affects price/delivery/availability. | `supplier_quote.apply_update` | Yes | Applied fields, source response ref. |
| `quote.sent` | Customer-facing commercial commitment. | `quote.send` | Yes | Quote version, channel boundary, snapshot ref. |
| `quote.exported` | Export can expose customer/commercial data. | `quote.export` | Yes | Format, quote version, redaction policy. |
| `agent_output.accepted` | Candidate AI output enters workflow. | `agent.accept_output` | Yes | AgentRun ref, validation status, reviewer ref. |
| `matcher.decision_overridden` | Overrides backend decision service. | `matcher.override_decision` | Yes | Old decision, new decision, reason. |
| `permission.granted` | Privilege escalation risk. | `admin.permissions_manage` | Yes | Target actor, permission, scope, expiry if any. |
| `counterparty.exported` | Customer/counterparty base leakage risk. | `counterparty.export` | Yes | Export scope, filter summary, row count if safe. |
| `counterparty_enrichment.applied` | External/enriched data changes registry. | `counterparty.enrichment_apply` | Yes | Changed field names, source ref, reviewer. |
| `purchase.created` | Purchase workflow starts financial/procurement path. | `purchase.create` | Yes | Source request/quote/supplier refs if any. |

## Security And Privacy Rules

- Never put secrets, tokens, passwords, API keys, mail credentials, private keys, model paths, or full prompts in audit metadata.
- Use references and safe summaries instead of full request bodies, raw emails, source documents, or raw agent outputs.
- Store hashes for network/user-agent context unless future security policy requires raw values.
- Redact sensitive commercial details in audit views unless the viewer has matching permissions.
- Permission-denied events must avoid revealing whether a restricted object exists when that would leak information.
- Audit export requires elevated permission and its own audit event.

## Analytics, SLA, Notifications, And Quality Feeds

Audit/event data can feed future backend services, but only after permission and masking rules are enforced.

| Consumer | Events that can feed it | Notes |
| --- | --- | --- |
| Dashboards | request state changes, quote sent/accepted/rejected, supplier waiting, tender decisions, matcher outcomes | Analytics must respect permissions and freshness. |
| SLA | request created/assigned/status changed, supplier waiting, customer waiting, quote approval, tender deadline events | SLA pause/override must be audited. |
| Notifications | assignment, status change, supplier response received, quote approval required, tender needs_review, document publication | Notification previews must be permission-aware. |
| Audit reports | all sensitive events, denied access, grant/revoke, export, publish/unpublish | Export requires elevated permission. |
| Manager performance | request assignment, first response, quote sent, overdue, SLA breach | Staff performance visibility is sensitive. |
| Tender quality | tender candidate classification, manager keep/skip/needs_review decisions | Tender Reader output remains candidate data. |
| Product Selector quality | agent validation errors, manager corrections, matcher override/reject outcomes | Group by prompt/model/agent version. |
| Counterparty import quality | previewed, validated, applied, partially_applied, failed, merge reviewed | Helps review import mapping and duplicate handling. |

## Retention And Immutability Considerations

Future implementation should decide concrete retention periods. Until then, use these readiness rules:

- Security, permission, export, publish, supplier apply, quote send, and matcher override events require long retention.
- Routine read events may have shorter retention unless sensitive.
- Audit events should be append-only with correction events rather than in-place mutation.
- Redaction policy must support safe UI display and stricter export policy.
- Deleting a business entity should not delete its audit history without a separate retention/legal policy.

## Implementation Notes For Future Backend Tasks

- Emit events inside backend services after authorization and after successful state transition.
- Emit denied-access events without running business actions.
- Include `request_id` for API correlation and `idempotency_key` for mutating actions.
- Include `source_agent_run` when a business decision uses LLM candidate data.
- Include `permission_used` for sensitive reads and all mutating operations.
- The event names in this document are readiness contracts and can later become constants or persisted taxonomy rows.

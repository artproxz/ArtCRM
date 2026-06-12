# Permission Matrix And Access-Control Implementation Readiness

This document defines the implementation-readiness permission matrix for ArtCRM before backend authorization code is written.

It is documentation only. It does not implement backend authorization, middleware, API routes, database schema, SQL, ORM, migrations, frontend UI, tests, dependencies, containers, integrations, real data, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM will contain customer requests, request positions, catalog data, stock, prices, supplier discounts, purchase prices, quotes, supplier responses, documents, internal messages, agent output, matcher decisions, tenders, counterparties, purchases, and analytics. These areas must not be protected by role labels alone.

The goal of this document is to give future backend tasks a stable permission vocabulary and matrix that can be used to implement access checks, response masking, audit events, and transition guards.

## Core Principle

Roles are templates, not hardcoded limits.

Effective access is calculated as:

```text
effective_access = role_template_permissions
  + explicit_grants
  - explicit_revokes
  + object_ownership_checks
```

Rules:

- Frontend visibility is not authorization.
- Backend enforcement is required for every read, write, export, publication, state transition, sensitive field view, agent action, matcher action, and service actor action.
- Every sensitive grant, revoke, denied access, and sensitive permission use must emit an audit event.
- A `manager` may receive selected director/admin functions through explicit grants.
- A `manager_assistant` may receive manager functions or elevated functions through explicit grants.
- An `administrator` does not automatically see commercial-sensitive data.
- A `director` may have oversight permissions but may lack operational edit permissions if they are not explicitly granted.
- A `service_actor` receives only scoped workflow permissions needed for agents, import jobs, matchers, generators, schedulers, and future integrations.

## Role Templates

| Role template | Default intent | Important limits |
| --- | --- | --- |
| `administrator` | Technical access administration, user support, account lifecycle, technical audit. | No automatic purchase price, supplier discount, margin, supplier response, customer base export, quote send, or commercial document access. |
| `director` | Business oversight, approvals, sensitive commercial review when granted. | No automatic operational edit/send/import/delete actions unless explicit permissions grant them. |
| `manager` | Daily CRM request, quote, supplier, catalog review, customer communication, and internal workflow. | Sensitive commercial, export, override, audit, and admin functions require explicit grants. |
| `manager_assistant` | May share the manager baseline or a reduced/elevated subset. | Must not be hardcoded as permanently weaker than manager. Differences are grants/revokes. |
| `customer` | Authenticated customer with own-only MVP access to carts, requests, quote history, and customer-visible documents. | Cannot view internal CRM threads, supplier responses, purchase prices, supplier discounts, margins, or other customers' data. |
| `guest` | Unauthenticated public catalog browsing. | Cannot add to cart, submit request, upload files, view history, view personal terms, or create persistent customer-owned data. |
| `service_actor` | Backend jobs, agents, import runners, matchers, generators, schedulers, integrations. | Scoped, least-privilege, auditable access only; no broad human-style access. |

## Permission Families

The following permission families are the baseline vocabulary for future implementation:

- `request.*`
- `request_position.*`
- `catalog.*`
- `stock.*`
- `pricing.*`
- `matcher.*`
- `agent.*`
- `quote.*`
- `supplier_quote.*`
- `documents.*`
- `messenger.*`
- `notifications.*`
- `sla.*`
- `analytics.*`
- `tender.*`
- `customer.*`
- `customer_organization.*`
- `counterparty.*`
- `purchase.*`
- `admin.*`
- `audit.*`

`counterparty.*` and `purchase.*` are included now because the next implementation group is expected to cover amoCRM counterparty import, counterparty search, enrichment, merge review, and purchase workflows.

## Matrix Conventions

Cell values:

- `Yes` - included in the default template.
- `No` - not included by default.
- `Own` - only objects owned by the current customer/user.
- `Assigned` - only assigned staff work.
- `Team` - staff team scope when object scope allows it.
- `Explicit` - available only through explicit grant.
- `Scoped` - service actor can use only within a backend-controlled workflow scope.

## Permission Matrix

| Permission | Entity | Action | Default administrator | Default director | Default manager | Default manager assistant | Default customer | Default guest | Service actor | Can be granted | Can be revoked | Sensitive | Audit required | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `request.view_assigned` | RequestCard | View assigned requests | Explicit | Yes | Yes | Yes | No | No | Scoped | Yes | Yes | No | Yes | Staff assignment scope. |
| `request.view_team` | RequestCard | View team requests | Explicit | Yes | Explicit | Explicit | No | No | Scoped | Yes | Yes | No | Yes | Team scope must be backend-filtered. |
| `request.view_all` | RequestCard | View all staff requests | Explicit | Yes | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Can expose customer base and commercial context. |
| `request.create` | RequestCard | Create request draft | No | Explicit | Yes | Yes | Own | No | Scoped | Yes | Yes | No | Yes | Customer-created requests are own-only. |
| `request.edit` | RequestCard | Edit request fields | No | Explicit | Assigned | Assigned | Own limited | No | Scoped | Yes | Yes | No | Yes | Backend validates state and ownership. |
| `request.assign_manager` | RequestCard | Assign/reassign responsible manager | Explicit | Yes | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Assignment affects SLA and workload. |
| `request.change_status` | RequestCard | Change workflow status | Explicit | Explicit | Assigned | Assigned | No | No | Scoped | Yes | Yes | Yes | Yes | Must pass state machine guards. |
| `request.archive` | RequestCard | Archive request | Explicit | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Archive preserves audit history. |
| `request.export` | RequestCard | Export request data | Explicit | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | Sensitive export if customer/commercial data included. |
| `request_position.create` | RequestPosition | Create position draft | No | Explicit | Assigned | Assigned | Own limited | No | Scoped | Yes | Yes | No | Yes | Agent-created drafts require validation. |
| `request_position.edit` | RequestPosition | Edit candidate/normalized fields | No | Explicit | Assigned | Assigned | Own limited | No | Scoped | Yes | Yes | No | Yes | Changes can affect matching and quote. |
| `request_position.approve` | RequestPosition | Approve validated position | No | Explicit | Assigned | Assigned | No | No | No | Yes | Yes | Yes | Yes | Approval enables downstream quote/matcher use. |
| `catalog.view` | CatalogItem | View public/published catalog | Yes | Yes | Yes | Yes | Yes | Yes | Scoped | Yes | Yes | No | Optional | Guest sees public fields only. |
| `catalog.view_private_fields` | CatalogItem | View internal catalog fields | Explicit | Explicit | Yes | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Includes internal catalog metadata. |
| `catalog.import` | CatalogPublication | Import catalog source | Explicit | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Source files remain backend-controlled. |
| `catalog.publish` | CatalogPublication | Publish catalog version | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Publication changes matcher source. |
| `catalog.rollback_version` | CatalogPublication | Roll back catalog version | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | High-risk source-of-truth action. |
| `stock.view` | StockSnapshot | View stock/availability | Explicit | Yes | Yes | Explicit | Public only | Public only | Scoped | Yes | Yes | No | Optional | Public visibility depends on policy. |
| `stock.import` | StockSnapshot | Import stock source | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Stock does not create catalog identity. |
| `stock.publish` | StockSnapshot | Publish stock snapshot | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Affects availability and delivery labels. |
| `pricing.view_customer_price` | PriceSnapshot | View customer-facing price | Explicit | Yes | Yes | Explicit | Own visible | Public policy | Scoped | Yes | Yes | Yes | Yes | Only if price policy exposes it. |
| `pricing.view_purchase_price` | PriceSnapshot | View purchase price | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive permission. |
| `pricing.view_supplier_discount` | PriceSnapshot | View supplier discount | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive permission. |
| `pricing.view_margin` | QuoteLine | View margin | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive analytics/commercial permission. |
| `pricing.apply_manual_discount` | QuoteLine | Apply manual discount | No | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | May require approval. |
| `pricing.override_price` | QuoteLine | Override customer price | No | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | State and approval guarded. |
| `matcher.run` | CatalogMatcherRun | Run matcher | No | Explicit | Yes | Yes | No | No | Scoped | Yes | Yes | No | Yes | Uses validated candidate data only. |
| `matcher.view_result` | CatalogMatcherRun | View matcher result | Explicit | Yes | Yes | Yes | No | No | Scoped | Yes | Yes | No | Yes | Hide internal audit if not permitted. |
| `matcher.override_decision` | CatalogMatcherRun | Override matcher decision | No | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | High-risk action; requires reason. |
| `agent.run` | AgentRun | Request backend agent execution | No | Explicit | Yes | Explicit | No | No | Scoped | Yes | Yes | No | Yes | Frontend never calls Ollama directly. |
| `agent.view_output` | AgentRun | View safe agent output | Explicit | Yes | Yes | Yes | No | No | Scoped | Yes | Yes | Yes | Yes | Raw/full prompt remains hidden. |
| `agent.accept_output` | AgentRun | Accept validated candidate output | No | Explicit | Assigned | Assigned | No | No | No | Yes | Yes | Yes | Yes | Agent output is never final truth by itself. |
| `quote.create_draft` | Quote | Create quote draft | No | Explicit | Assigned | Assigned | No | No | Scoped | Yes | Yes | Yes | Yes | Uses confirmed request/catalog data. |
| `quote.edit` | Quote | Edit quote draft/lines | No | Explicit | Assigned | Assigned | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive fields masked by permissions. |
| `quote.request_approval` | Quote | Request approval | No | Yes | Assigned | Assigned | No | No | No | Yes | Yes | Yes | Yes | May trigger notification/SLA. |
| `quote.approve` | Quote | Approve quote/discount | No | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | Not all directors auto-approve without grant. |
| `quote.send` | Quote | Send customer-facing quote | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sent quote is immutable or revised. |
| `quote.export` | QuoteVersion | Export quote/PDF/Excel | No | Explicit | Explicit | Explicit | Own visible | No | Scoped | Yes | Yes | Yes | Yes | Export may expose customer/commercial data. |
| `supplier_quote.create_request` | SupplierQuoteRequest | Create supplier draft | No | Explicit | Assigned | Assigned | No | No | Scoped | Yes | Yes | Yes | Yes | Draft must be reviewed before send. |
| `supplier_quote.send_request` | SupplierQuoteRequest | Send supplier request | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | No credentials in docs/UI. |
| `supplier_quote.view_response` | SupplierQuoteResponse | View supplier response | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive commercial data. |
| `supplier_quote.apply_update` | SupplierQuoteResponse | Apply price/delivery/availability update | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Cannot silently update customer data. |
| `documents.create_metadata` | Document | Create document record | Explicit | Explicit | Assigned | Assigned | Own limited | No | Scoped | Yes | Yes | No | Yes | File upload/storage remains future. |
| `documents.view_internal` | Document | View internal document | Explicit | Explicit | Assigned | Assigned | No | No | Scoped | Yes | Yes | Yes | Yes | Internal documents never leak to customers. |
| `documents.publish_customer_visible` | Document | Publish to customer-visible scope | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Explicit publication transition required. |
| `documents.download` | DocumentVersion | Download permitted document | Explicit | Explicit | Assigned | Assigned | Own visible | Public only | Scoped | Yes | Yes | Yes | Yes | Download audit required for sensitive docs. |
| `messenger.view_thread` | MessageThread | View internal thread | Explicit | Explicit | Entity scope | Entity scope | No | No | Scoped | Yes | Yes | Yes | Yes | Entity permission and messenger permission both required. |
| `messenger.create_message` | Message | Create internal message | Explicit | Explicit | Entity scope | Entity scope | No | No | Scoped | Yes | Yes | No | Yes | Internal only, not customer chat. |
| `messenger.export` | MessageThread | Export messages | No | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | Can expose commercial/customer data. |
| `notifications.view` | Notification | View own notifications | Yes | Yes | Yes | Yes | Own | No | Scoped | Yes | Yes | No | Optional | Notification preview must be masked. |
| `notifications.manage_rules` | NotificationRule | Manage notification rules | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Can affect other users. |
| `sla.view` | SLAAlert | View SLA alerts | Explicit | Yes | Assigned | Assigned | No | No | Scoped | Yes | Yes | No | Yes | Visibility follows entity scope. |
| `sla.pause` | SLAAlert | Pause/resume SLA | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Requires reason and audit. |
| `sla.override` | SLAAlert | Override SLA breach/rule | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | High-risk operational action. |
| `analytics.view_own` | Analytics | View own dashboard | No | Yes | Yes | Yes | No | No | Scoped | Yes | Yes | No | Optional | Staff performance details need extra permission. |
| `analytics.view_staff_performance` | Analytics | View staff performance | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Sensitive management data. |
| `analytics.export_sensitive` | Analytics | Export sensitive analytics | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Includes margin/customer/staff data risk. |
| `tender.view` | TenderCandidate | View tender candidates | Explicit | Yes | Yes | Explicit | No | No | Scoped | Yes | Yes | No | Yes | Tender Reader output is candidate data. |
| `tender.classify` | TenderCandidate | Keep/skip/needs_review decision | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Backend/manager final decision. |
| `tender.export` | TenderCandidate | Export tender data | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Buyer/tender data may be sensitive. |
| `customer.view_own` | Customer | View own profile/history | No | No | No | No | Own | No | No | Yes | Yes | No | Optional | Customer MVP is own-only. |
| `customer.view_all` | Customer | View customer registry | Explicit | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Customer base export risk. |
| `customer.support_access` | Customer | Staff support access to customer context | Explicit | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | Staff support access must be audited. |
| `customer_organization.view_org` | CustomerOrganization | View org-shared context | No | No | No | No | Future explicit | No | No | Yes | Yes | Yes | Yes | Future, not MVP default. |
| `customer_organization.invite_user` | CustomerOrganization | Invite org user | No | No | No | No | Future explicit | No | No | Yes | Yes | Yes | Yes | Deferred implementation. |
| `counterparty.search` | Counterparty | Search counterparties | Explicit | Yes | Yes | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Required for future ART-60+ work. |
| `counterparty.import_preview` | CounterpartyImport | Preview import | Explicit | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Preview does not mutate registry. |
| `counterparty.import_apply` | CounterpartyImport | Apply validated import | No | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Import application is high risk. |
| `counterparty.export` | Counterparty | Export counterparty data | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Customer base leakage risk. |
| `counterparty.enrichment_apply` | CounterpartyEnrichment | Apply enrichment changes | No | Explicit | Explicit | No | No | No | Scoped | Yes | Yes | Yes | Yes | Must be reviewable, no silent overwrite. |
| `purchase.view` | Purchase | View purchases | Explicit | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Purchase is not quote/request/supplier quote. |
| `purchase.create` | Purchase | Create purchase draft | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Future procurement workflow. |
| `purchase.update` | Purchase | Update purchase | No | Explicit | Explicit | Explicit | No | No | Scoped | Yes | Yes | Yes | Yes | Requires state guards. |
| `purchase.export` | Purchase | Export purchase data | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Commercial-sensitive. |
| `admin.users_manage` | User | Manage users/account states | Yes | Explicit | Explicit | Explicit | No | No | No | Yes | Yes | Yes | Yes | Manager/admin functions can be granted flexibly. |
| `admin.permissions_manage` | Permission | Grant/revoke permissions | Yes | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Every grant/revoke is audited. |
| `audit.view` | AuditEvent | View audit events | Yes | Explicit | Explicit | Explicit | Own visible | No | Scoped | Yes | Yes | Yes | Yes | Scope depends on entity and sensitivity. |
| `audit.export` | AuditEvent | Export audit events | No | Explicit | Explicit | No | No | No | No | Yes | Yes | Yes | Yes | Audit export is high risk. |

## Sensitive Permissions

The following permissions or data views require explicit attention in backend implementation:

- Purchase price: `pricing.view_purchase_price`.
- Supplier discount: `pricing.view_supplier_discount`.
- Margin: `pricing.view_margin`.
- Supplier quote response: `supplier_quote.view_response`.
- Quote approval: `quote.approve`.
- Manual discount: `pricing.apply_manual_discount`.
- Sensitive export: `request.export`, `quote.export`, `analytics.export_sensitive`, `counterparty.export`, `audit.export`, `purchase.export`.
- Customer-visible document publication: `documents.publish_customer_visible`.
- Internal commercial documents: `documents.view_internal`, `documents.download` for commercial-sensitive scope.
- Staff performance analytics: `analytics.view_staff_performance`.
- Permission management: `admin.permissions_manage`.
- Audit export: `audit.export`.
- Agent output acceptance: `agent.accept_output`.
- Matcher override: `matcher.override_decision`.
- Counterparty export: `counterparty.export`.
- Counterparty enrichment apply: `counterparty.enrichment_apply`.
- Purchase creation/update: `purchase.create`, `purchase.update`.

## Object Ownership Rules

### Staff Assigned

A staff user may act on a request, quote, supplier quote, document, message thread, or notification when the object is assigned to them and the permission allows assigned scope.

### Staff Team

Team access is broader than assigned access and must be explicit. Team-scoped views must still mask sensitive fields unless the user also has the specific sensitive permission.

### All Staff With Permission

All-staff or all-business visibility requires permissions such as `request.view_all`, `customer.view_all`, or `analytics.view_staff_performance`. These permissions are sensitive and must be audited when used for broad access.

### Customer Own-Only

MVP customer access is own-only:

- own carts;
- own requests;
- own quote history;
- own customer-visible documents;
- own profile data.

A customer must not see another customer's requests, carts, documents, quote history, internal comments, internal threads, supplier responses, purchase prices, supplier discounts, or margins.

### Customer Organization Future Shared

Organization-shared access is future architecture. It must not be treated as MVP default. When implemented, organization access must be permission-checked through `customer_organization.*` and object ownership rules.

### Service Actor Scoped Access

Service actors must be scoped by workflow:

- import runners can read their source and write import results;
- agents can read only backend-selected input references;
- Catalog Matcher can read validated candidate data and catalog publications;
- document generators can read only approved quote/version data;
- schedulers can create permitted notifications/reminders/SLA events;
- future integrations can access only their integration scope.

### Internal-Only Data

Internal-only data includes internal messages, supplier responses, commercial-sensitive documents, matcher audit details, agent prompts/raw output where restricted, purchase price, supplier discount, margin, and staff performance analytics. These fields require explicit permissions and masking.

### Customer-Visible Data

Customer-visible data must be produced by explicit backend publication, quote send/export, or customer-safe catalog publication. Customer-visible status may differ from internal status.

## API Response Masking Rules

Backend APIs must mask sensitive fields by permissions. Frontend hiding is insufficient.

Examples:

- Do not return `purchase_price` without `pricing.view_purchase_price`.
- Do not return `supplier_discount` without `pricing.view_supplier_discount`.
- Do not return `margin` without `pricing.view_margin`.
- Do not return internal document links without `documents.view_internal` or equivalent document scope.
- Do not allow all-counterparty export without `counterparty.export`.
- Do not return staff performance analytics without `analytics.view_staff_performance`.
- Do not return supplier quote response details without `supplier_quote.view_response`.
- Do not return matcher override controls without `matcher.override_decision`.
- Do not return permission management controls without `admin.permissions_manage`.
- Do not return customer organization shared data unless organization membership and `customer_organization.*` permissions allow it.
- Do not reveal sensitive notification previews when the user cannot access the target entity or field.

Suggested masking representation:

```json
{
  "customer_price": "visible-value-placeholder",
  "purchase_price": null,
  "purchase_price_masked": true,
  "supplier_discount": null,
  "supplier_discount_masked": true,
  "margin": null,
  "margin_masked": true,
  "masking_reason": "permission_required"
}
```

## Implementation Notes For Future Backend Tasks

- Permission checks should happen before business service execution and before serialization.
- Serialization should apply field-level masking after entity-level authorization.
- Mutating operations should require `idempotency_key` where repeated calls can create duplicate effects.
- Every denied sensitive access should emit `permission_denied` audit event without exposing restricted content.
- Every allowed sensitive access should emit an audit event when the action can materially expose or change sensitive business data.
- Permission names in this document are contracts for future implementation and may be mapped to constants or database rows later.

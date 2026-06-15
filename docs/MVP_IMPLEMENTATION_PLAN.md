# MVP Implementation Plan And Task Slicing Before Code

This document is documentation only. It does not implement backend code, frontend code, API routes, database schema, SQL, ORM models, migrations, Alembic files, tests, integrations, dependencies, containers, `.env.example` changes, real data, prices, customer/counterparty data, credentials, tokens, secrets, business logic, or actual Linear issue creation.

## 1. Executive Summary

ArtCRM architecture readiness is mostly complete for a controlled backend-first MVP, but implementation should start only after this plan is reviewed and accepted. The current architecture already defines the critical boundaries: backend is the source of truth, LLM agents produce candidate data only, permissions and audit are mandatory, state machines guard workflow changes, and API contracts define the frontend/backend boundary.

The first MVP should focus on staff-side CRM and controlled request processing: request cards, request positions, counterparty context, ROSMA catalog data, Product Selector candidate review, Backend Catalog Matcher decisions, supplier quote registration, and quote lifecycle foundations. Customer marketplace work should start only after request/catalog/matcher foundations are stable enough to handle customer-created demand safely.

ART-56, ART-57, ART-58, ART-59, ART-60, ART-61, ART-62, and ART-63 are now architecture inputs for implementation planning. ART-64 is the final documentation/planning step before creating real code tasks. Future code tasks listed here are proposals only; real Linear issues must be created separately after ART-64 is reviewed.

## 2. Implementation Principles

1. Backend first, UI second.
2. Permissions before sensitive data.
3. Audit before analytics.
4. State machines before workflow UI.
5. API contracts before frontend screens.
6. Import preview before import apply.
7. Catalog import before matcher.
8. Product Selector candidate storage before matcher acceptance.
9. Supplier response apply before quote finalization.
10. Quote versioning before customer-facing quote export.
11. Customer marketplace after staff-side processing basics.
12. No LLM as final business truth.
13. No silent mutation of sensitive commercial data.
14. No frontend-only authorization.
15. No customer-visible publication without explicit backend transition.
16. No real external integrations until local/domain flows are stable.
17. No broad MVP; first MVP must be intentionally narrow.

## 3. Strict MVP Scope

The MVP is not the full product. It should include only the smallest backend-first path that can process controlled staff-side requests and later support a minimal customer catalog/request quote flow.

Strict MVP includes:

- backend permission/audit foundation;
- state transition guard foundation;
- common API response envelope and error model;
- request card and request position backend;
- counterparty registry import preview/apply foundation;
- counterparty search/profile read foundation;
- ROSMA catalog import/read foundation;
- stock/price snapshot import/read foundation;
- Product Selector candidate output storage/review;
- Backend Catalog Matcher MVP;
- staff workspace backend endpoints;
- supplier quote draft/manual response registration;
- supplier quote reviewed apply;
- quote draft/version/line lifecycle;
- minimal quote approval/send boundary;
- minimal customer catalog/cart/request quote flow;
- document metadata/link/publish boundary, minimal;
- basic notification event generation, not full notification engine.

## 4. Explicitly Postponed Scope

The following scope is intentionally postponed until the backend MVP foundations are stable:

- full customer organization sharing;
- advanced marketplace UX;
- realtime messenger;
- OCR/document parsing;
- automatic supplier email sending;
- tender platform scraping/integration;
- automatic bid submission;
- 1C runtime integration;
- PDF/KP generator if quote lifecycle is not stable yet;
- BI dashboards;
- advanced analytics;
- advanced notification preferences/quiet hours;
- AI customer assistant full UI;
- manager assistant advanced workflows;
- multi-manufacturer adapters beyond ROSMA MVP;
- automated enrichment API integration if free/legal source is not confirmed;
- auto-merge of counterparties;
- automatic purchase creation from quote without review;
- direct customer self-checkout/payment;
- automatic final analog selection by LLM;
- automatic legal/risk scoring of counterparties.

## 5. Backend-First Implementation Strategy

Implementation should start with backend modules, DTOs, permissions, audit, and state guards. Minimal persistence and services should exist before broad UI work begins, and APIs should be exposed only after state, permission, idempotency, and audit rules are known.

Frontend should consume backend-masked DTOs. It must not calculate final permissions, margins, supplier discounts, final matcher decisions, quote status, customer-visible document visibility, or sensitive publication state. Frontend can request operations and display allowed states, but backend owns authorization, masking, state transitions, audit, and business truth.

The repository currently contains architecture documentation and backend boundary placeholders for catalog/matcher-related modules. Future implementation tasks may evolve those modules, but ART-64 does not modify code. First code PRs must be small and foundation-focused; a broad “full CRM screen” should not begin before backend primitives exist.

## 6. Recommended Phase Sequence

### Phase 0 — Readiness Gate

Purpose: confirm documents and constants before coding.

Must verify:

- permission names;
- audit event names;
- state names;
- API group names;
- entity naming;
- MVP scope;
- data source assumptions;
- first code slice.

Output: future implementation tickets only.

### Phase 1 — Security, Audit, State Foundation

Code later:

- Permission Decision Service;
- Audit/Event Service;
- State Transition Guard utility;
- Common API response envelope;
- Common error model;
- Idempotency helper;
- Service actor boundaries.

Do not build UI here.

### Phase 2 — Request Backend Foundation

Code later:

- RequestCard;
- RequestPosition;
- assignment;
- source references;
- statuses;
- position review;
- link to AgentRun;
- link to Counterparty.

### Phase 3 — Counterparty Backend Foundation

Code later:

- Counterparty registry persistence;
- CounterpartyImport preview/apply;
- amoCRM ID external refs;
- duplicate candidate detection;
- search/profile read;
- manual update;
- enrichment preview/apply boundary;
- purchase draft link boundary.

### Phase 4 — Catalog / Stock / Price Foundation

Code later:

- ROSMA catalog import;
- catalog publication;
- catalog item read/search;
- stock snapshot;
- price snapshot;
- delivery estimate policy;
- internal vs public fields.

### Phase 5 — Agent Output And Product Selector Foundation

Code later:

- AgentRun storage;
- Product Selector candidate storage;
- validation status;
- review/accept/reject;
- no final truth from LLM.

### Phase 6 — Backend Catalog Matcher MVP

Code later:

- matcher request/response;
- decision enum;
- matched/missing/mismatched fields;
- no_match/needs_review/blocked;
- manager accept/reject/override;
- audit.

### Phase 7 — Staff Workspace Backend MVP

Code later:

- manager inbox;
- assigned/team/open/overdue/waiting_supplier/waiting_customer/quote_draft/tenders;
- request detail aggregation;
- counters;
- quick actions as backend operations;
- permission-masked DTOs.

### Phase 8 — Supplier Quote MVP

Code later:

- supplier quote request draft;
- manual response registration;
- apply reviewed supplier price/delivery/availability;
- no silent customer-facing update.

### Phase 9 — Quote / Commercial Offer MVP

Code later:

- quote draft;
- quote version;
- quote lines;
- manual discount;
- approval;
- send boundary;
- export boundary;
- customer-facing snapshot.

### Phase 10 — Minimal Customer Marketplace MVP

Code later:

- public catalog browse/search;
- guest read-only catalog;
- auth-before-cart;
- cart;
- request quote from cart;
- customer own requests/quotes/documents.

### Phase 11 — Hardening And Expansion

Code later:

- document storage;
- notification runtime;
- analytics;
- marketplace UX expansion;
- counterparty enrichment integration;
- 1C integration;
- tender monitor;
- realtime messaging.

## 7. Dependency Graph

| Slice | Depends on | Unlocks | Risk if skipped |
| --- | --- | --- | --- |
| Permission foundation | Accepted permission names and role/grant model | All sensitive APIs, masking, service actors | Sensitive data can leak or actions become frontend-only authorization. |
| Audit foundation | Permission foundation and event taxonomy | Analytics, SLA, security review, support history | Later analytics and incident review become unreliable. |
| State guards | State machine contracts and permissions | Workflow endpoints, quote/request transitions, document publication | Invalid states can be reached and UI workflows become inconsistent. |
| Request backend | Common envelope, permissions, audit, state guards | Product Selector, matcher inputs, staff workspace | Agents and matcher lack stable request/position anchors. |
| Counterparty registry | Permissions, audit, state guards | Customer/company context, purchases, imports, enrichment | Requests and purchases cannot be linked to reliable CRM identities. |
| Catalog import | Product type profiles, source mapping, publication rules | Catalog read/search, matcher source of truth | Matcher may operate on dirty or unversioned catalog data. |
| Product Selector output | AgentRun storage, request positions, JSON schemas | Matcher request inputs and manager candidate review | LLM data may bypass validation or be lost without audit trail. |
| Matcher | Catalog import, Product Selector candidates, permissions, audit | Quote line confidence and manager approval decisions | Quote lines may rely on unverified or mismatched items. |
| Supplier quote | Requests, catalog/matcher, supplier response permissions | Accurate price/delivery/availability inputs for quote | Quotes may be finalized with stale or unsupported supplier data. |
| Quote lifecycle | Request, matcher, supplier response, pricing permissions | Customer-facing offer, quote versions, export boundary | Customer offers may be mutable, unaudited, or commercially unsafe. |
| Customer marketplace | Catalog, auth, cart/request creation, permissions | Customer self-service request quote flow | Customer demand may enter the system without backend control. |
| Document visibility | Permissions, audit, document metadata | Safe publication/download of customer/internal documents | Internal files may become customer-visible without explicit transition. |
| Analytics | Audit/events and stable entity states | Dashboards, SLA metrics, management views | Dashboards become ad-hoc raw queries over unstable business data. |

## 8. Backend Module Ownership

| Module | Owns | Does not own | Key entities | Key permissions | Audit events | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| `auth/permissions` | Effective access, grants, revokes, object scope, service actor permission checks. | Business workflow decisions or UI visibility policy. | User, RoleTemplate, PermissionGrant, PermissionRevoke, ServiceActor. | `admin.*`, all domain permission checks. | `permission.*`, `permission.denied`. | User identity and audit. |
| `audit` | Append-only event records, safe event payloads, audit reads by entity. | Business state mutation or analytics calculations. | AuditEvent. | `audit.view`. | All event families. | Permissions and actor context. |
| `workflow/state_machine` | Transition validation utilities and state guard decisions. | Entity persistence or UI routing. | TransitionRule, StateTransitionResult. | Uses domain permissions. | `state_transition.*`, domain state events. | Permissions, audit, entity state. |
| `requests` | RequestCard lifecycle, assignment, source refs, aggregate request state. | Catalog matching, quote pricing, customer org sharing. | RequestCard. | `request.*`. | `request.*`. | Permissions, audit, state guards, counterparties. |
| `request_positions` | RequestPosition lifecycle, candidate/validated product lines, review state. | Final catalog decision or price calculation. | RequestPosition. | `request_position.*`, `matcher.*`. | `request_position.*`. | Requests, agents, matcher, audit. |
| `counterparties` | Counterparty profile, contacts, addresses, external refs, merge review. | Customer auth accounts or legal risk conclusions. | Counterparty, CounterpartyContact, CounterpartyAddress, CounterpartyExternalRef. | `counterparty.search`, `counterparty.update`, `counterparty.merge_review`, `counterparty.export`. | `counterparty.created`, `counterparty.updated`, `counterparty.merge_candidate_reviewed`. | Permissions, audit, import, enrichment. |
| `counterparty_import` | Import batches, preview/apply, amoCRM external refs, duplicate candidates. | CSV UI upload implementation or automatic merge. | CounterpartyImport, CounterpartyImportRow, DuplicateCandidate. | `counterparty.import_preview`, `counterparty.import_apply`, `counterparty.merge_review`. | `counterparty_import.*`. | Counterparties, audit, state guards. |
| `counterparty_enrichment` | Enrichment request/preview/apply boundary and source timestamps. | Scraping, paid providers, legal scoring. | CounterpartyEnrichment. | `counterparty.enrichment_request`, `counterparty.enrichment_apply`, `counterparty.update`. | `counterparty_enrichment.*`, `counterparty.updated`. | Counterparties, audit, permissions. |
| `purchases` | Purchase draft, lifecycle, lines, counterparty links, sensitive procurement fields. | Quote approval, supplier quote collection, 1C runtime. | Purchase, PurchaseLine. | `purchase.view`, `purchase.create`, `purchase.update`, `purchase.approve`, `purchase.export`. | `purchase.*`. | Counterparties, documents, supplier quotes, pricing permissions. |
| `catalog` | Catalog identity, product type profiles, publication versions, public/private catalog fields. | Stock quantity, customer price, LLM candidate extraction. | CatalogItem, CatalogPublication, ProductTypeFilterProfile. | `catalog.*`. | `catalog.*`. | Source mapping, audit, state guards. |
| `stock` | Stock snapshots, availability labels, stock publication. | Catalog identity or customer pricing. | StockSnapshot. | `stock.*`. | `stock.*`. | Catalog, audit. |
| `pricing` | Price snapshots, customer/purchase price visibility, margin masking policy. | Supplier negotiation workflow or quote version state. | PriceSnapshot, PricingPolicy. | `pricing.*`. | `pricing.*`. | Catalog, stock, permissions, audit. |
| `delivery` | Delivery estimate policy and delivery candidate/snapshot values. | Supplier quote response registration or logistics integration. | DeliveryEstimatePolicy, DeliverySnapshot. | Uses catalog/quote/supplier visibility permissions. | `delivery.*` or domain events. | Catalog, stock, supplier quotes. |
| `agents` | AgentRun persistence, prompt/model metadata, candidate output envelope, validation status. | Final business decisions or direct Ollama access from frontend. | AgentRun, AgentOutput. | `agent.run`, `agent.view_output`, `agent.accept_output`. | `agent_run.*`, `agent_output.*`. | Permissions, audit, backend agent runtime. |
| `product_selector` | Product Selector candidate storage/review and ROSMA-specific intent DTOs. | Catalog item approval, matcher decision, pricing. | ProductSelectorCandidate, RelatedComponentSuggestion. | `agent.*`, `request_position.*`. | `agent_output.*`, `request_position.*`. | Agents, requests, catalog profiles, matcher. |
| `matcher` | Backend Catalog Matcher runs, decisions, mismatch/no_match/needs_review/blocked results. | LLM prompting, price approval, catalog import. | CatalogMatcherRun, MatcherCandidate. | `matcher.run`, `matcher.view_result`, `matcher.override_decision`. | `matcher.*`. | Catalog, request positions, product selector, audit. |
| `supplier_quotes` | Supplier quote draft, manual response registration, reviewed apply. | Automatic supplier email integration or customer quote mutation. | SupplierQuoteRequest, SupplierQuoteResponse. | `supplier_quote.*`. | `supplier_quote.*`. | Requests, quote drafts, pricing, audit. |
| `quotes` | Quote drafts, versions, lines, approval/send/export boundaries. | Supplier response acquisition, document storage implementation. | Quote, QuoteVersion, QuoteLine. | `quote.*`, `pricing.*`. | `quote.*`. | Requests, matcher, supplier quotes, documents. |
| `documents` | Document metadata, versions, links, visibility/publish boundary. | File storage provider implementation or PDF business generation. | Document, DocumentVersion, DocumentLink. | `documents.*`. | `documents.*`. | Permissions, audit, quotes, requests. |
| `notifications` | Notification events, reminder scheduling boundary, SLA alert hooks. | Full realtime delivery or advanced preferences in MVP. | Notification, Reminder, SLAAlert. | `notifications.*`, `sla.*`. | `notification.*`, `sla.*`. | Audit/events, workflow states. |
| `analytics` | Read models/projections from audit/events and stable states. | Mutating business entities or ad-hoc raw sensitive export. | AnalyticsProjection. | `analytics.*`. | `analytics.*`, sensitive read events. | Audit, permissions, stable states. |
| `customer_portal` | Customer-safe catalog/cart/request quote APIs and own-data views. | Staff workspace, all-counterparty search, internal documents. | Cart, CartLine, CustomerRequestView. | `customer.*`, `catalog.view`, `quote.export` own visible. | `customer.*`, request/quote events. | Auth, catalog, requests, documents. |
| `staff_workspace` | Manager inbox aggregation, counters, quick action orchestration, permission-masked DTOs. | Source-of-truth business logic or frontend authorization. | StaffInboxView, RequestDetailView. | Uses request, quote, supplier, tender, counterparty, document permissions. | Domain events for quick actions. | Requests, quotes, supplier quotes, counterparty, audit. |

## 9. API Group Implementation Order

| Order | API group | Why in this order | Depends on | Not before |
| --- | --- | --- | --- | --- |
| 1 | Auth/current user/effective permissions | Frontend and services need a safe access snapshot before sensitive reads. | User identity assumptions. | Sensitive domain APIs. |
| 2 | Audit append/read by entity | Mutations and sensitive reads need event emission from the start. | Actor context and permission checks. | Analytics, SLA, compliance-sensitive workflows. |
| 3 | Common API envelope and error model | All APIs should share response shape, errors, masked fields, and audit refs. | Permission/audit conventions. | Domain API proliferation. |
| 4 | State transition validation boundary | Workflow APIs need a single guard model before UI starts transitions. | State machines, permissions, audit. | Request/quote/document state endpoints. |
| 5 | RequestCard/RequestPosition | Core CRM intake anchors for agents, matcher, staff workspace, quotes. | Common envelope, permissions, audit, state guards. | Product Selector and matcher acceptance. |
| 6 | Counterparty import/search/profile | Requests need company/customer context, and imports need preview before apply. | Permissions, audit, request links. | Purchase and enrichment workflows. |
| 7 | Catalog read/search/import-publication | Matcher and marketplace require versioned catalog identity. | Catalog source mapping and product type profiles. | Matcher or marketplace cart. |
| 8 | Stock/price snapshot read/import | Quote and marketplace views need separated stock/price snapshots. | Catalog identity. | Supplier quote apply and quote pricing. |
| 9 | AgentRun/Product Selector | Candidate data must be persisted/reviewable before matcher consumes it. | Requests, positions, agent schemas. | Matcher acceptance. |
| 10 | Catalog Matcher | Converts validated candidates + catalog into backend decisions. | Catalog, Product Selector output, permissions, audit. | Quote line confidence. |
| 11 | Staff workspace aggregation | Inbox needs stable request/counterparty/catalog/matcher data. | Request, counterparty, matcher APIs. | Broad CRM UI. |
| 12 | Supplier quote | Manual supplier response registration supports reliable price/delivery. | Requests, catalog, pricing, quote draft boundaries. | Quote finalization. |
| 13 | Quote lifecycle | Customer-facing offer depends on request, matcher, supplier, pricing state. | Supplier quote apply, matcher, document metadata boundary. | Customer-visible quote export. |
| 14 | Documents metadata/link/publish boundary | Quotes and requests need safe document visibility before publication. | Permissions, audit, quote lifecycle. | File storage/download expansion. |
| 15 | Customer catalog/cart/request quote | Marketplace can safely create demand after backend processing basics exist. | Auth, catalog, requests, quote boundary. | Advanced customer UX. |
| 16 | Notifications/analytics later | They should consume stable events and states rather than drive early domain shape. | Audit/events, stable state machines. | Foundation workflows. |

## 10. Database / Persistence Design Order

This is not schema implementation. It is only persistence design sequencing. Do not create actual schema, columns, SQL, migrations, ORM models, or Alembic files from this section without a separate code task.

Suggested conceptual design order:

1. users / roles / permissions / grants / revokes;
2. audit_events;
3. request_cards / request_positions;
4. counterparties / external_refs / contacts / addresses / import_batches / import_rows / duplicate_candidates;
5. catalog_items / catalog_publications / product_type_profiles;
6. stock_snapshots / price_snapshots / delivery_policies;
7. agent_runs / agent_outputs;
8. matcher_runs / matcher_candidates;
9. supplier_quote_requests / supplier_quote_responses;
10. quotes / quote_versions / quote_lines;
11. documents / document_versions / document_links;
12. purchases / purchase_lines;
13. carts / cart_lines / customer_requests;
14. notifications / reminders / SLA alerts;
15. analytics projections later.

## 11. Migration Order

Do not write migration files from this plan. Do not define actual DDL here. The batches below describe only conceptual migration sequencing.

| Batch | Purpose | Depends on | Rollback consideration | Seed/dev data policy |
| --- | --- | --- | --- | --- |
| Batch A: permission/audit base | Establish roles, permissions, grants/revokes, audit event storage. | Accepted permission matrix and audit taxonomy. | Rollback must not orphan audit refs in later batches. | Demo permissions only; no production secrets. |
| Batch B: request/counterparty base | Add request cards, positions, counterparties, external refs, import review data. | Batch A. | Preserve audit history and external refs on rollback planning. | Synthetic demo counterparties only; no real customer data. |
| Batch C: catalog/stock/price | Add catalog identity, product type profiles, publication, stock and price snapshots. | Batch A and request/counterparty anchors if linking is needed. | Catalog publications need version rollback strategy. | Synthetic or approved fixture data only; no real prices unless separately approved. |
| Batch D: agent/matcher | Add AgentRun, agent outputs, matcher runs and candidates. | Batches A-C. | Agent outputs remain candidate/audit data and can be archived safely. | Synthetic agent fixtures only; no full prompts or secrets. |
| Batch E: supplier quote/quote | Add supplier quote requests/responses and quote versions/lines. | Batches A-D. | Sent quote immutability must survive rollback planning. | Demo commercial values only; no real customer prices. |
| Batch F: documents/purchases | Add document metadata/version/link records and purchase lines. | Batches A-E. | Document visibility and purchase-sensitive fields need careful rollback. | Placeholder metadata only; no real files or supplier docs. |
| Batch G: customer portal/cart | Add carts, cart lines, customer-owned request/quote views. | Auth, catalog, request, quote foundations. | Customer ownership refs must remain consistent. | Demo customer accounts only; no real personal data. |
| Batch H: notifications/analytics projections | Add notification/reminder/SLA tables and analytics projections. | Stable audit/events and entity states. | Projections can be rebuilt from events when possible. | Synthetic event samples only. |

All batches must avoid real customer data, production secrets, credentials, tokens, private keys, production prices, and production emails.

## 12. Testing Strategy

Future implementation should include the following tests. No tests are implemented in this PR.

- permission matrix tests;
- permission masking tests;
- explicit grant/revoke tests;
- audit event emission tests;
- state transition tests;
- idempotency tests;
- import preview tests;
- duplicate detection tests;
- catalog import tests;
- stock/price snapshot tests;
- Product Selector candidate contract tests;
- matcher decision tests;
- supplier quote apply tests;
- quote version immutability tests;
- customer ownership tests;
- document visibility tests;
- API contract tests;
- regression fixtures.

Testing should start with backend unit and contract tests for permission/audit/state primitives, then expand to domain service tests, API tests, and regression fixtures. Frontend tests should begin after backend APIs and masked DTOs are stable.

## 13. Acceptance Criteria Per Slice

### Permission / Audit / State Foundation

- unauthorized sensitive read is denied or masked;
- mutating action emits an audit event;
- state transition is denied if invalid;
- explicit grant/revoke changes effective access;
- service actor scoped access is enforced.

### Request Backend Foundation

- manager can create/update assigned request;
- request position can be reviewed;
- state guards prevent invalid quote-ready state;
- audit events are emitted.

### Counterparty Import

- preview does not mutate registry;
- amoCRM ID idempotency works;
- missing INN row is not auto-merged;
- duplicate INN creates review candidate;
- apply emits audit.

### Catalog / Stock / Price

- catalog import publication is separated from stock snapshot;
- stock does not create catalog identity;
- customer price, purchase price, supplier discount, and margin are permission-masked.

### Product Selector / AgentRun

- LLM output is stored as candidate data;
- candidate output can be accepted/rejected;
- accepted candidate does not equal final business truth.

### Catalog Matcher

- LLM output alone cannot approve item;
- mismatch blocks or needs review;
- override requires permission and reason.

### Supplier Quote

- supplier response is registered manually;
- supplier response does not silently update customer-facing quote;
- apply action is audited.

### Quote Lifecycle

- sent quote is immutable;
- new version is required for changes;
- approval and send require permissions.

### Customer Marketplace

- guest cannot add to cart;
- customer sees own data only;
- customer cannot enumerate counterparties;
- request quote from cart creates controlled request.

## 14. Proposed Future Code Tasks

The tasks below are proposed draft slices only. They are not created in Linear by this PR and must be reviewed before real task creation.

### Must-have MVP code tasks

| Draft task | Purpose | Depends on | Deliverables | Acceptance criteria | Out of scope |
| --- | --- | --- | --- | --- | --- |
| `ART-CODE-001: Implement Permission Decision Service` | Compute effective permissions from role template, grants, revokes, ownership, and service actor scope. | Accepted permission matrix. | Backend service/interface, permission fixtures, masking helper boundary. | Sensitive action is denied/masked without permission; grant/revoke changes effective access. | Full UI, admin console, unrelated domains. |
| `ART-CODE-002: Implement Audit Event Service` | Append safe audit events for mutations and sensitive reads. | ART-CODE-001, audit taxonomy. | Audit append/read-by-entity service, safe payload rules. | Mutations emit audit refs; secrets/full prompts are not stored. | Analytics dashboards, log shipping. |
| `ART-CODE-003: Implement State Transition Guard Utility` | Enforce workflow state transitions consistently. | ART-CODE-001, ART-CODE-002, state machines. | Transition guard utility, denied transition error shape. | Invalid transition is rejected with audit-safe error. | Full workflow engine UI. |
| `ART-CODE-004: Implement Common API Envelope, Error Model And Idempotency Helper` | Standardize responses, errors, masked fields, audit refs, and idempotency. | ART-CODE-001..003. | Envelope DTOs, error types, idempotency helper boundary. | Mutating duplicate requests are idempotent or conflict safely. | Business routes beyond examples. |
| `ART-CODE-005: Implement RequestCard And RequestPosition Persistence` | Store request and position lifecycle anchors. | ART-CODE-001..004. | Persistence models/services for RequestCard and RequestPosition. | Assigned manager can create/update; invalid states blocked; audit emitted. | Agent execution, matcher, quote UI. |
| `ART-CODE-006: Implement Counterparty Registry Persistence` | Store counterparties, contacts, addresses, and external refs. | ART-CODE-001..005. | Counterparty persistence/service layer. | Counterparty profile can be stored and linked to request with audit. | CSV parser, enrichment integration. |
| `ART-CODE-007: Implement amoCRM CSV Import Preview` | Preview amoCRM company CSV without mutating registry. | ART-CODE-006. | Import batch/row preview service, validation report. | Preview reports missing INN, invalid contacts, unknown mappings, and duplicate candidates. | Import apply, real CSV committed to repo. |
| `ART-CODE-008: Implement Counterparty Duplicate Candidate Detection` | Detect reviewable duplicate candidates. | ART-CODE-006, ART-CODE-007. | Duplicate candidate rules by amoCRM ID, INN, normalized legal name, contact signals. | Missing INN never auto-merges by name; duplicate INN requires review. | Automatic merge. |
| `ART-CODE-009: Implement Counterparty Search/Profile Read API` | Expose manager-facing registry search and profile DTOs. | ART-CODE-006, ART-CODE-008. | Search/list/profile APIs with permission masking. | Managers can search permitted fields; customers cannot enumerate counterparties. | UI and export. |
| `ART-CODE-010: Implement ROSMA Catalog Import Preview/Apply` | Import and publish ROSMA catalog data with product type profiles. | ART-CODE-001..004, catalog docs. | Catalog import preview/apply services, publication boundary. | Import preview validates product-type filters; apply creates versioned publication. | Multi-manufacturer adapters. |
| `ART-CODE-011: Implement Stock And Price Snapshot Import` | Store stock/price snapshots separately from catalog identity. | ART-CODE-010. | Stock and price snapshot services/read APIs. | Stock does not create catalog identity; sensitive prices are masked. | Live supplier integration. |
| `ART-CODE-012: Implement AgentRun Persistence` | Store auditable AgentRun metadata and candidate outputs. | ART-CODE-005, agent docs. | AgentRun persistence/service, prompt/model fields, validation status. | Agent output stored as candidate data with safe summaries. | Calling Ollama or prompt registry UI. |
| `ART-CODE-013: Implement Product Selector Candidate Review API` | Review, accept, or reject Product Selector candidate data. | ART-CODE-012, ART-CODE-005. | Candidate review endpoints/service. | Accepted candidate remains not final business truth and is auditable. | Catalog item approval or price calculation. |
| `ART-CODE-014: Implement Backend Catalog Matcher MVP` | Match validated candidate positions against catalog with decision enum. | ART-CODE-010..013. | Matcher request/response, decisions, mismatch details, override path. | LLM output alone cannot approve; mismatch blocks/needs review; override requires reason. | Advanced analog ranking. |
| `ART-CODE-015: Implement Staff Workspace Request Inbox API` | Aggregate staff-side request queues and counters. | ART-CODE-005, 009, 014. | Manager inbox/detail DTOs, quick action boundaries. | DTOs are permission-masked and reflect backend state. | Full CRM frontend screen. |
| `ART-CODE-016: Implement Supplier Quote Draft And Manual Response API` | Register supplier quote drafts and manual responses. | ART-CODE-005, 010, 011, 014. | Supplier quote draft/response services and APIs. | Manual response apply is audited and does not silently update customer quote. | Automatic supplier email sending. |
| `ART-CODE-017: Implement Quote Draft, Version And Line Lifecycle` | Create quote drafts, versions, lines, approval/send boundary. | ART-CODE-014, ART-CODE-016. | Quote services/APIs, version immutability rules. | Sent quote immutable; changes require new version; approval/send permission enforced. | PDF generator and payment. |
| `ART-CODE-018: Implement Document Metadata And Visibility API` | Link documents to entities and control internal/customer-visible publication. | ART-CODE-017. | Document metadata/version/link APIs and visibility guard. | Customer-visible publication requires explicit transition and audit. | File storage/download implementation. |
| `ART-CODE-019: Implement Minimal Customer Catalog Browse/Search API` | Provide safe public/customer catalog read endpoints. | ART-CODE-010, ART-CODE-011, auth foundation. | Public catalog browse/search APIs with public/private field split. | Guest sees public fields only and cannot mutate data. | Advanced marketplace UX. |
| `ART-CODE-020: Implement Auth-Before-Cart And Request Quote From Cart` | Allow authenticated customers to create carts and controlled request quote. | ART-CODE-019, ART-CODE-005, ART-CODE-017. | Cart/cart line APIs and request quote creation boundary. | Guest cannot add to cart; customer sees own data only; request quote creates controlled request. | Self-checkout/payment and organization sharing. |

### Should-have after MVP

| Proposed task | Purpose | Depends on | Deliverables | Acceptance criteria | Out of scope |
| --- | --- | --- | --- | --- | --- |
| Customer organization sharing | Share selected carts/requests/quotes inside customer organization. | Customer auth, own-only customer portal, permissions. | Organization roles, invite/join rules, shared visibility DTOs. | No customer can see unrelated organization data. | Broad B2B account management. |
| Notification runtime | Deliver reminders, SLA alerts, and event notifications. | Audit/events, stable states, notification architecture. | Scheduler/dispatcher boundary and user notification read model. | Notifications are permission-masked and idempotent. | Advanced preferences/quiet hours. |
| Analytics projections | Build dashboards from audit/events and stable state transitions. | Audit taxonomy, stable workflows, permission masking. | Projection jobs/read APIs. | Dashboards never bypass sensitive permissions. | BI warehouse. |
| Document storage/download | Store and download files with visibility controls. | Document metadata API. | Storage adapter, download authorization, antivirus/check hooks if selected. | Internal documents do not leak to customers. | OCR/parsing. |
| Quote PDF/export generator | Generate customer-facing quote/KP snapshots. | Stable quote lifecycle and document visibility. | Backend generator/template output boundary. | Generated file uses confirmed quote version only. | AI-generated sums or pricing. |
| Enrichment integration if legal/free source confirmed | Fetch public counterparty data from legal/free sources. | Counterparty enrichment boundary and legal review. | Source adapter, preview/apply, rate limits. | No silent overwrite; source timestamp stored. | Paid dependency or scraping without legal approval. |
| Marketplace UX expansion | Improve customer catalog/cart/request workflows. | Minimal customer APIs. | Additional frontend/backend UX features. | Customer own-data boundary stays enforced. | Self-checkout/payment. |
| Staff messenger runtime | Implement internal message/thread runtime. | Staff workspace, document permissions. | Thread/message APIs, entity links, notifications. | Internal messages are staff-only and audited where required. | Realtime infrastructure if not selected. |

### Postponed / later

| Proposed task | Purpose | Depends on | Deliverables | Acceptance criteria | Out of scope |
| --- | --- | --- | --- | --- | --- |
| 1C runtime integration | Exchange confirmed documents/data with 1C. | Stable quote/purchase/document lifecycle. | Backend-only integration adapter and audit. | No frontend direct 1C access; failures are auditable. | Early MVP. |
| OCR/document parser | Extract data from uploaded files. | Document storage and validation policy. | Parser pipeline and reviewable candidate data. | Extracted data is candidate and reviewable. | Direct business mutation. |
| Tender platform integration/scraping | Monitor/import tender data where legal. | Tender Reader rules and legal review. | Integration adapter or manual import boundary. | No automatic bid submission. | Unsupported scraping. |
| Automatic supplier email integration | Send/receive supplier quote emails. | Supplier quote manual workflow stable. | Backend mail adapter and audit. | No credentials in repo; manual review remains possible. | Direct frontend mail access. |
| Realtime messaging | Push live staff/customer events. | Messenger runtime and notification runtime. | Realtime transport adapter. | Permissions enforced server-side. | Core MVP. |
| BI dashboards | Advanced management analytics. | Analytics projections and stable events. | BI-ready datasets/dashboard APIs. | Sensitive metrics require permissions. | Raw database shortcuts. |
| Multi-manufacturer adapters | Support manufacturers beyond ROSMA. | ROSMA import/matcher stable and adapter pattern accepted. | Manufacturer-specific rulebooks/parsers/profiles. | Rules do not become falsely universal. | First MVP. |
| Advanced customer assistant UI | Customer-facing AI help and guided selection. | Marketplace foundations and agent validation. | Assistant UX and backend validation path. | AI output remains candidate and cannot approve items. | Unvalidated final advice. |
| Automatic legal/risk scoring | Score counterparties legally/commercially. | Enrichment integration and legal policy. | Reviewable risk candidate data. | No automatic legal conclusion. | MVP and unreviewed external data. |

## 15. Release Milestones

### Milestone M0 — Architecture freeze

All required architecture docs are merged, ART-64 is accepted, and real code tasks are created separately.

### Milestone M1 — Backend foundation

Permissions, audit, states, common API envelope, error model, idempotency, and service actor boundaries exist.

### Milestone M2 — CRM request/counterparty foundation

Requests, positions, counterparties, import preview/apply, duplicate candidates, search/profile reads, and enrichment boundary are in place.

### Milestone M3 — Catalog/matcher foundation

ROSMA catalog import/publication, stock/price snapshots, AgentRun/Product Selector candidate review, and Backend Catalog Matcher MVP are in place.

### Milestone M4 — Staff quote workflow

Supplier quote drafts/manual responses, quote draft/version/line lifecycle, approval/send boundaries, and minimal staff inbox are in place.

### Milestone M5 — Customer catalog MVP

Public catalog browse/search, auth-before-cart, cart, and request quote from cart are in place with own-data boundaries.

### Milestone M6 — Hardening

Documents, notifications, analytics, enrichment integration, 1C later, and broader UX/runtime improvements are added after MVP foundations are stable.

## 16. Risk-Based Sequencing

- RBAC late -> implement permission service first.
- Audit late -> analytics/security unreliable.
- UI before API -> frontend work duplicated.
- Catalog before import rules -> bad matcher.
- Matcher before Product Selector contracts -> unreliable inputs.
- Quote before supplier response apply -> wrong prices/schedules.
- Marketplace before staff workflow -> customer requests go nowhere.
- Counterparty import without preview -> duplicated dirty data.
- Enrichment integration before legal review -> source/legal risk.
- 1C early -> integration chaos.
- PDF/KP generator too early -> incorrect quote snapshots.
- Analytics too early -> dashboards based on unstable events.
- Purchase flow too early -> confusion between quote/request/purchase.

## 17. Ready-To-Code Gate

The team can start code only when:

- all architecture docs are merged;
- ART-56/57/58/59/60/61/62/63/64 are Done;
- permission names are stable;
- audit event families are stable;
- state names are stable;
- API group order is accepted;
- strict MVP scope is accepted;
- postponed scope is accepted;
- first code slice is selected;
- real code tasks are created separately;
- no unresolved high-risk architecture contradictions remain.

Do not start code if:

- permission names still mismatch;
- MVP includes too much UI;
- catalog import assumptions are unclear;
- counterparty import rules are unclear;
- sensitive fields are not classified;
- state transitions are not accepted;
- first code task tries to implement multiple business domains at once.

## 18. Definition Of Done For First Backend MVP

The first backend MVP is done only when:

- permission checks exist on sensitive endpoints;
- audit events are emitted for mutations and sensitive reads;
- state transitions are enforced;
- request and position lifecycle works;
- counterparty import preview/apply is minimal but controlled;
- ROSMA catalog and stock/price snapshot flow is minimal but usable;
- Product Selector candidate review is stored;
- matcher returns decisions;
- staff can create quote draft;
- supplier response can be manually registered and applied;
- customer can browse catalog and send request quote from cart;
- no secrets are committed;
- tests cover permission/state/import/matcher/quote basics;
- documentation is updated with implementation details.

## 19. Final Recommendation

Proceed to code only after this plan is accepted. Start with backend foundation, not UI. Create real future Linear/code tasks from the proposed task list only after review. The first coding PR should be small and must not implement broad business UI.

Recommended first code bundle:

`Permission Decision Service + Audit Event Service + State Transition Guard Utility + Common API Envelope/Error Model/Idempotency Helper`

Even this bundle should be sliced small enough to review safely. If the first implementation PR becomes too large, start with `ART-CODE-001: Implement Permission Decision Service`, then add audit, state guards, and common API primitives in separate reviewable PRs.

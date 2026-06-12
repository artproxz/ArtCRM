# Final Architecture Review Before Business Implementation

This document performs the final documentation-only architecture review for ArtCRM before business implementation starts.

It reviews the current pre-implementation architecture coverage across CRM, marketplace, catalog, AI agents, backend-only services, commercial workflows, supplier workflows, documents, notifications, analytics, security, and tender processing.

No backend code, frontend code, database schema, SQL, ORM, migrations, tests, integrations, containers, dependencies, real data, credentials, tokens, secrets, prices, or customer data are added by this review.

## 1. Executive Summary

ArtCRM has enough documented architecture to start controlled implementation planning, but it should not jump directly into broad business logic implementation.

Final verdict: partially ready for implementation. The system is architecturally aligned around the correct principles, but several implementation contracts must be made explicit before coding high-risk business behavior.

Strong points already covered:

- Backend is the only trusted boundary for Ollama, mail, 1C, database access, catalog matching, pricing, documents, secrets, and integrations.
- LLM agents produce candidate data only.
- Backend validation and manager review own business decisions.
- Product Selector is limited to ROSMA-specific candidate extraction and related-component suggestions until future manufacturer adapters exist.
- Backend Catalog Matcher is a backend service, not an LLM agent.
- KP, invoice, PDF, and document generation belong to backend generators/templates based on confirmed data.
- Security/RBAC is permission-based, not hardcoded by role names.
- Guest, customer, staff, and service/system actor boundaries are documented separately.
- Staff workspace, marketplace, supplier quote workflow, document center, notifications/SLA, analytics, and Tender Reader mode are covered at architecture level.

Important blockers before business implementation:

- Define a concrete permission matrix and audit event taxonomy.
- Freeze request, quote, supplier quote, document, and notification state machines.
- Convert conceptual DTOs into implementation-ready API contracts.
- Define persistence ownership for core entities without leaking frontend-only assumptions into backend logic.
- Decide MVP scope so the first implementation does not attempt the full CRM, marketplace, agents, documents, analytics, and tender system at once.

Recommended next step: create an implementation-readiness task that converts this architecture into an MVP build plan with explicit backend modules, API contracts, state transitions, permission checks, and acceptance criteria.

## 2. Current Architecture Coverage

| Area | Existing coverage | Coverage status | Remaining decision before implementation |
| --- | --- | --- | --- |
| Core architecture and domain model | `ARCHITECTURE.md`, `DOMAIN_MODEL.md` | Covered conceptually | Finalize entity ownership and lifecycle guards. |
| API contracts and request lifecycle | `API_CONTRACTS.md`, `REQUEST_LIFECYCLE.md` | Covered conceptually | Convert to route-level contracts and error models. |
| Agent platform | `AGENT_PLATFORM.md`, `AGENT_RUN.md`, `AGENT_JSON_SCHEMAS.md` | Strongly covered | Implement validation service and prompt/model registry later. |
| Product Selector | Eval, rulebook, fixtures, related components | Strongly covered for ROSMA | Future manufacturer adapters and automated evaluation runner. |
| Catalog model | `CATALOG_MODEL.md`, `CATALOG_SOURCE_MAPPING.md` | Strongly covered | Parser profile implementation and publication process. |
| ROSMA import | `ROSMA_CATALOG_IMPORT_PLAN.md` | Covered for MVP | Decide exact file formats, validation, versioning, and rollback UI. |
| Catalog Matcher | `CATALOG_MATCHER.md`, `CATALOG_MATCHER_API.md` | Strongly covered | Implement deterministic decision rules and audit records. |
| Catalog persistence | `CATALOG_DATABASE_MODEL.md` | Conceptual coverage | Translate to schema only after MVP persistence task. |
| Security/RBAC | `SECURITY_RBAC_ARCHITECTURE.md` | Strongly covered | Concrete permission matrix, grant/revoke workflows, audit format. |
| Customer auth and guest access | `CUSTOMER_AUTH_AND_GUEST_ACCESS.md` | Covered | Decide auth mechanism and account recovery policy. |
| Internal communication | `CRM_TASK_MESSENGER.md` | Covered conceptually | Decide realtime/scheduler/file implementation later. |
| Customer marketplace | `CUSTOMER_MARKETPLACE_PORTAL.md` | Covered conceptually | Decide MVP customer catalog/search/cart subset. |
| Customer organizations | `CUSTOMER_ORGANIZATION_ACCESS.md` | Future model covered | Keep own-only MVP unless organization sharing is explicitly prioritized. |
| Staff workspace | `STAFF_WORKSPACE_AND_PIPELINE.md` | Covered conceptually | Freeze pipeline statuses and action permissions. |
| Notifications/SLA | `NOTIFICATIONS_REMINDERS_SLA.md` | Covered conceptually | Runtime scheduler, SLA pause rules, escalation rules. |
| Analytics | `CRM_ANALYTICS_DASHBOARDS.md` | Covered conceptually | Define metrics from implemented entities only. |
| Commercial offer | `COMMERCIAL_OFFER_LIFECYCLE.md` | Covered conceptually | Quote state machine, snapshot rules, approval thresholds. |
| Supplier quote | `SUPPLIER_QUOTE_WORKFLOW.md` | Covered conceptually | Manual registration first; email/API automation later. |
| Document center | `CRM_DOCUMENT_CENTER.md` | Covered conceptually | Storage, scanning, versioning, visibility enforcement. |
| Tender Reader | `TENDER_READER_RULES.md` | Covered conceptually | Keep as Mail Reader mode until tender volume justifies a separate service. |

## 3. Manager / Staff CRM Functional Map

The staff CRM surface is documented as an operational command center rather than a single request form.

Manager and manager assistant functions:

- Work with new requests, assigned requests, overdue requests, blocked requests, waiting supplier, waiting customer, waiting manager action, quote drafts, supplier responses, tenders, reminders, mentions, and internal tasks.
- Open request cards created from mail, customer marketplace carts, manual entry, or future tender workflows.
- Review Mail Reader candidate extraction before saving business data.
- Review Product Selector candidate data and decide whether clarification is needed.
- Run or inspect Backend Catalog Matcher results when permissions allow.
- Accept, reject, or override matcher decisions only through permissioned backend actions.
- Create supplier quote request drafts from validated request/catalog data.
- Review supplier response data before applying price, delivery, or availability updates.
- Create KP drafts from validated catalog, price, delivery, supplier, and request data.
- Edit quote lines, discounts, comments, and customer-facing text only within explicit permissions.
- Send or export customer-facing quote versions only after approval rules allow it.
- Use internal chats linked to request, quote, supplier quote, tender, matcher execution, import review, or task context.
- Create reminders and react to SLA alerts when permissions allow.
- View dashboards scoped by own/team/all permissions.

Director functions:

- View business overview, request funnel, SLA risk, quote conversion, supplier bottlenecks, tender outcomes, product demand, and commercial-risk widgets when granted.
- Approve sensitive quote actions, manual discounts, price overrides, exports, and commercial document publication when policy requires it.
- Grant/revoke high-risk permissions when allowed by access-management policy.
- Review audit and staff performance where explicitly permitted.

Administrator functions:

- Manage user access, account states, technical audit, and support flows.
- Help with access problems and support channels.
- Does not automatically see purchase prices, margins, supplier discounts, supplier responses, customer commercial history, or internal business threads unless explicitly granted.

Service/system actor functions:

- Run backend jobs, import runners, validators, matchers, schedulers, and future integrations with least-privilege permissions.
- Must be auditable like human actors where business state can be affected.

## 4. Customer Marketplace / Catalog Functional Map

Guest functions:

- Browse public catalog.
- Search catalog.
- Open public product cards.
- View public documents if published.
- Cannot add to cart, submit request, request KP, upload files, see personal terms, view history, see internal fields, or create persistent customer-owned data.

Authenticated customer functions:

- Add products to cart.
- Save and submit cart/request.
- Request commercial offer/KP.
- View own carts, own requests, and own quote history.
- Repeat previous requests only after revalidation of catalog, availability, delivery, and price visibility.
- Upload specifications only when future policy and document security are implemented.

Customer organization future functions:

- Multiple customer users may exist under one organization.
- Organization roles can include organization admin, purchaser, engineer, approver, accountant, and viewer.
- MVP remains own-only unless organization sharing is explicitly implemented.
- Organization sharing must never bypass backend ownership and permission checks.

Marketplace/catalog functions:

- Public product cards can expose public technical characteristics, related accessories, compatible components, public documents, and delivery labels if policy allows.
- Internal fields such as purchase price, supplier discount, margin, matcher audit, supplier response, and internal comments are not customer-visible.
- Product comparison, favorites, repeat requests, customer dashboards, and upload lists are future features and must respect customer auth boundaries.

## 5. AI Agent Functional Map

| Agent or service | Type | Allowed output | Not allowed | Status |
| --- | --- | --- | --- | --- |
| Mail Reader Agent | LLM agent | Candidate email/request extraction | Direct business saves without backend validation | Existing/documented model boundary. |
| Tender Reader mode | LLM agent mode/subtype | Candidate tender metadata and relevance classification | Bids, pricing, scraping, KP/PDF, final keep/skip decision | Documented target mode. |
| Product Selector Agent | LLM agent | Candidate product intent, ROSMA model candidate, missing fields, warnings, related-component suggestions | Approving catalog item, prices, discounts, delivery, KP/PDF/email | Needs quality evaluation; ROSMA-only scope. |
| Client Catalog Assistant | Future LLM assistant | Customer-facing explanation and guided selection drafts | Confirming SKU, stock, price, delivery, analogs as facts | Target/future only. |
| Manager Catalog Assistant | Future LLM assistant | Staff-facing explanations and selection help | Backend decisions, price calculation, PDF generation | Target/future only. |
| Response Draft Agent | Future LLM agent | Draft text for response to customer | Totals, VAT, prices, requisites, final PDF, email send | Target/future only. |
| Future Tender Monitor Agent | Future agent/service | Monitoring-oriented tender signals if justified later | Scraping or bidding without separate architecture | Deferred. |
| Backend Catalog Matcher | Backend-only service | Validated/decision data for catalog match | LLM-style free generation | Documented as backend service. |
| Invoice/PDF/KP Generator | Backend-only generator/template/script | Customer-facing generated documents from confirmed data | LLM final calculations or direct agent output | Future backend boundary. |
| Agent Validation Service | Backend-only service | Validation results, errors, sanitization | Business decisions without configured rules | Future implementation need. |
| Agent Orchestrator | Backend-only service | Controlled agent execution and AgentRun records | Direct access to secrets or unchecked persistence | Future implementation need. |

Cross-cutting agent rules:

- LLM output is always candidate data.
- Backend validates agent output before saving to business entities.
- `model_name` is a model name such as an Ollama/API model name, never a filesystem path.
- Agent outputs, summaries, prompts, and errors must not reveal secrets, credentials, tokens, private keys, full prompts, model paths, or sensitive customer data.
- Agent errors must not block the whole request card; they create reviewable states and retry/fallback opportunities.

## 6. Backend Service Boundary Map

Backend is the only trusted access point for:

- Ollama and any future model runtime/API.
- Mailbox/IMAP/Exchange/Gmail or any future mail integration.
- 1C integration.
- Database and cache/queue.
- Catalog import, stock import, price import, publication, rollback, and audit.
- Catalog Matcher and analog/related-component decisions.
- Supplier quote draft, response registration, and apply actions.
- KP, invoice, PDF, Excel, and document generation.
- File storage, download, publication, scanning, parsing, and OCR.
- Authentication, authorization, permission checks, and audit.
- Notification, reminder, SLA, and scheduler runtimes.

Service boundary assessment:

| Backend service area | Responsibility | Must not do |
| --- | --- | --- |
| Catalog service | Store and expose published catalog identity and public/private fields | Treat unvalidated LLM output as catalog truth. |
| Catalog import service | Parse manufacturer/source files by product-type profile | Use one universal regex for all product types. |
| Stock service | Store stock snapshots and availability signals | Overwrite catalog identity with daily stock rows. |
| Pricing service | Own customer/purchase price, discount, margin, and visibility rules | Expose sensitive prices without permission. |
| Delivery estimate service | Derive customer/internal delivery labels from validated data | Let LLM or frontend invent delivery facts. |
| Catalog Matcher | Decide exact/compatible/analog/no-match outcomes from validated data | Calculate prices, generate PDFs, or call 1C. |
| Supplier quote service | Draft requests, register responses, apply approved updates | Silently update quote/customer fields from supplier email. |
| Quote service | Own KP lifecycle, versions, approvals, customer snapshot | Let Response Draft Agent create final commercial numbers. |
| Document service | Own file metadata, versions, visibility, publication, retention | Make chat attachments customer-visible automatically. |
| Permission service | Enforce RBAC and ownership checks | Delegate authorization truth to frontend. |
| Agent orchestration/validation | Run agents, store AgentRun, validate candidate data | Let agents bypass permissions or secrets boundaries. |

## 7. Catalog / Matcher / Stock / Price / Delivery Coverage

Catalog model coverage is strong and implementation-ready at concept level.

Important decisions already documented:

- Catalog identity is separated from stock, prices, discounts, delivery, and supplier quote responses.
- Product types have product-type-specific filter profiles with `required`, `optional`, `derived`, and `not_applicable` fields.
- Product Selector and Catalog Matcher must not treat all fields as universal.
- The parser should classify product type/product kind first, then apply the matching parsing/filter profile.
- ROSMA catalog/stock import is the MVP manufacturer path.
- Non-ROSMA manufacturers need future manufacturer-specific adapters/rulebooks.
- Stock snapshots and daily stock uploads are separate from catalog item identity.
- Purchase prices, supplier discounts, margins, and customer prices are sensitive commercial data.
- Delivery estimate is a backend-derived, policy-controlled result, not LLM output.

Catalog Matcher readiness:

- Backend Catalog Matcher is correctly defined as a deterministic backend service boundary.
- It consumes validated Product Selector candidate data and catalog data.
- It can produce decisions such as exact match, compatible exact, analog candidate, needs review, no match, or blocked.
- It must record audit, inputs, rules/profile versions, and warnings.
- It must not approve Product Selector output without backend validation.

Open catalog decisions:

- Exact catalog source format and import runner behavior.
- Publication and rollback UI/API scope.
- Price list source format, customer price policies, and manual discount approval thresholds.
- Delivery estimate rules and supplier confirmation flow.
- Analog ranking and compatibility thresholds.

## 8. Commercial Workflow Coverage

Commercial offer/KP lifecycle is covered conceptually and should become one of the first implementation contracts after permissions and request state machine.

Covered decisions:

- KP is separate from cart and request.
- KP has versions and customer-facing snapshots.
- Sent KP should be immutable or revised through a new version.
- Quote lines reference request positions, validated catalog items, matcher executions, supplier responses, related components, and service positions.
- Customer-facing fields must exclude purchase price, supplier discount, margin, internal comments, matcher audit, and supplier internals.
- Manual discounts, price overrides, export/send actions, and approval flows require explicit permissions.
- Response Draft Agent can draft wording only; it cannot calculate totals, VAT, prices, requisites, or create final PDFs.
- Final KP/PDF/Excel generation belongs to backend generator/template logic based on confirmed data.

Open decisions:

- Approval thresholds for discount/margin/price override.
- Exact quote state machine and transition guards.
- PDF/Excel template ownership and versioning.
- Customer-visible quote acceptance/rejection UX.
- 1C handoff payload and timing.

## 9. Supplier Quote Workflow Coverage

Supplier quote architecture is covered as a controlled draft/response/apply workflow.

Covered decisions:

- Supplier quote request starts as a draft for manager review.
- Request line items should use validated catalog/request data.
- Hydrofilling and other service positions can be included as linked service-position lines.
- Supplier response registration can be manual in MVP.
- Supplier response does not silently update request, quote, price, delivery, or customer-facing fields.
- Applying supplier price/delivery/availability updates requires explicit permission and audit.
- Supplier response documents and attachments are internal unless explicitly transformed into customer-facing data.

Open decisions:

- Manual-only MVP versus mailbox parsing/API integration.
- Supplier contact/address book model.
- Response due rules and SLA pause behavior.
- Which supplier response fields are enough to generate a KP version.
- How ROSMA-specific supplier workflow generalizes to other suppliers.

## 10. Document / File / Attachment Coverage

The document architecture correctly separates chat attachments from CRM document center objects.

Covered decisions:

- Document Center owns controlled document metadata, versions, visibility, retention, and audit.
- Chat attachments are message-linked files and do not automatically become customer-visible documents.
- Customer-visible publication is explicit.
- Commercial-sensitive, staff-sensitive, supplier-related, internal-only, public catalog, and restricted documents have separate visibility scopes.
- Future scanning, OCR, parsing, preview generation, malware scanning, and file storage require separate implementation tasks.
- Quote exports must reference quote version snapshots.
- Supplier responses and import files are internal unless explicitly transformed and published.

Open decisions:

- Storage backend and path/reference format.
- File scanning and quarantine policy.
- Document version retention and deletion policy.
- Preview/OCR/parser permissions.
- Customer upload limits and supported formats.

## 11. Communication Center Coverage

The internal CRM Communication Center is covered as a staff-only communication layer.

Covered decisions:

- It supports entity-linked work chats, direct staff chats, group staff chats, and support threads.
- Entity-linked chats can attach to request, cart, quote, supplier quote, tender, task, matcher execution, import review, and future custom contexts.
- Parent entity permissions and messenger permissions are both required.
- Internal CRM threads are not customer-facing chat.
- Direct/group chat access is participant- and permission-based.
- Attachments require separate security and file boundaries.
- Scheduled messages, auto-replies, rich text, emoji, unread counters, pinned chats, and search are future UI/runtime features.
- LLM agents do not read internal discussions unless explicitly permitted and justified.

Open decisions:

- Realtime transport versus polling.
- Message edit/delete retention and audit policy.
- Search indexing boundaries.
- Attachment storage and scanning.
- Whether customer-facing chat is needed later as a separate architecture.

## 12. Notifications / Reminders / SLA Coverage

Notification and SLA coverage is conceptually complete for architecture review.

Covered decisions:

- Notification Center is permission-aware.
- Notifications can target requests, assignments, status changes, supplier responses, quote approvals, customer replies, chat mentions, tenders, imports, reminders, SLA warnings, overdue states, and security notices.
- Notification previews must not reveal secrets or restricted commercial data.
- Reminders can target requests, quotes, supplier quote requests, customer replies, tenders, tasks, chats, and future entities.
- SLA concepts include first response, quote preparation, supplier response, tender deadline, approval due, warning threshold, overdue threshold, escalation, and pause reason.
- Quiet hours, mute, preferences, digest, and anti-spam boundaries are documented.

Open decisions:

- SLA formulas and pause/resume rules.
- Scheduler/runtime implementation.
- Escalation matrix and notification channels.
- Digest strategy and anti-notification-storm rules.
- How customer replies and supplier responses are detected in MVP.

## 13. Analytics / Dashboards Coverage

Analytics documentation is broad and should be implemented only after core workflows produce reliable events.

Covered decisions:

- Director, manager, manager assistant, and administrator dashboards have different permission-based scopes.
- Request funnel, response time, SLA, overdue, blocked, waiting supplier, quote conversion, tender, product demand, missing stock, import freshness, supplier response, marketplace activity, and internal communication/task events are candidate analytics sources.
- Margin, purchase price, supplier discount, sensitive exports, and staff performance are permission-protected and auditable.
- Analytics must identify time windows and data freshness.

Open decisions:

- Metrics definitions and source-of-truth events.
- Aggregation timing and freshness labels.
- Export formats and sensitive export permissions.
- Staff performance visibility policy.
- Whether analytics is MVP or post-MVP.

## 14. Tender Reader Coverage

Tender Reader is documented as a candidate-data mode/subtype of Mail Reader Agent.

Covered decisions:

- Tender Reader extracts candidate tender metadata and candidate relevance classification.
- It does not scrape platforms, download tender documents, submit bids, generate KP/PDF, calculate prices, or own final keep/skip decisions.
- Final tender decision belongs to backend rules and manager review.
- Initial focus is KIP/instrumentation categories and relevant manufacturers such as ROSMA, Fiztech, Manotom, and similar categories.
- Tender classification taxonomy includes keep, skip, needs_review, and blocked_irrelevant.
- Tender processing connects to staff workspace, notifications/SLA, analytics, commercial offer, supplier quote workflow, and document center.

Open decisions:

- Dedicated folder/label integration.
- Filter rules versioning and owner.
- Deadline urgency rules.
- Whether tender volume justifies a separate Tender Monitor Agent.
- Evaluation fixtures for tender relevance quality.

## 15. Security / RBAC / Permission Model Review

Security architecture is one of the strongest documented areas and should remain a hard gate for implementation.

Core principles:

- Roles are templates, not hardcoded limits.
- Effective access is role template permissions plus explicit grants minus explicit revokes.
- Frontend visibility is not authorization.
- Backend must enforce every read, write, export, publication, agent access, document access, and commercial action.
- Staff/customer/service actor boundaries are separate.
- Administrator does not automatically see commercial data.
- Director has broad business authority only where permissions grant it.
- Manager assistant may have the same functional baseline as manager if permissions allow.
- LLM agents and backend jobs are service/system actors with explicit least-privilege permissions.
- Permission grant/revoke/use for sensitive actions must be audited.

Permission families already identified:

- User and access management.
- Requests and CRM cards.
- Catalog and import/publication/rollback.
- Stock.
- Pricing and commercial fields.
- Cart, quote, and commercial offer.
- Supplier quote and ROSMA request.
- Product Selector and Catalog Matcher.
- Tenders.
- Internal messenger and files.
- Audit.
- Agents and service actors.
- Notifications, reminders, SLA, analytics, documents, and future customer organization permissions.

Security gaps before implementation:

- Concrete permission matrix by role template and entity/action.
- Audit event taxonomy and retention policy.
- Object-level ownership rules for customer, organization, request, quote, document, and chat contexts.
- Sensitive field masking policy for API responses.
- Service actor token/credential handling and rotation plan.

## 16. End-to-End Business Flows

### Flow A: Incoming Email To Request And KP

1. Backend receives/ingests controlled mail input.
2. Mail Reader Agent extracts candidate request data.
3. Backend validates candidate data and creates or updates a request card draft.
4. Manager reviews request card and positions.
5. Product Selector extracts candidate product intent per position.
6. Backend validation checks missing fields, forbidden mismatches, and manufacturer scope.
7. Backend Catalog Matcher decides catalog match or review state.
8. Manager handles exact match, analog candidate, no match, or needs review.
9. Supplier quote draft is created if price/delivery/availability confirmation is needed.
10. Supplier response is registered and applied by permissioned staff.
11. KP draft is generated from confirmed data.
12. Approval happens if needed.
13. Backend generator creates customer-facing KP/PDF/Excel snapshot.
14. Future 1C handoff happens only through backend integration after confirmed data.

### Flow B: Customer Marketplace To Staff Workspace

1. Guest browses public catalog.
2. Guest tries to add product to cart and must authenticate.
3. Authenticated customer adds items, submits cart/request, or requests KP.
4. Backend creates customer-owned request context.
5. Staff workspace shows item according to assignment, permission, priority, and SLA.
6. Manager reviews positions, validates product intent, runs matcher, and prepares KP.
7. Customer receives only customer-visible quote/documents/statuses.

### Flow C: Product Selection And Catalog Matching

1. RequestPosition contains source text and normalized candidate fields.
2. Product Selector proposes structured candidate intent.
3. Backend validation classifies missing fields, warnings, forbidden mismatches, and needs_review.
4. Catalog Matcher uses product-type-specific profiles and catalog data.
5. Backend records match decision, audit, profile versions, and confidence/reasoning.
6. Manager can accept, reject, or override only with permission.

### Flow D: Supplier Quote Loop

1. Manager creates supplier quote request draft from validated request/catalog data.
2. Manager reviews and sends later through a future controlled channel.
3. Request moves to waiting_supplier and SLA rules can pause/escalate.
4. Supplier response is registered manually in MVP or parsed later.
5. Applying price/delivery/availability updates requires permission and audit.
6. KP draft/quote line snapshots use applied confirmed data.

### Flow E: Tender Email To Review Decision

1. Tender notification arrives in a controlled tender folder/input source.
2. Tender Reader extracts candidate metadata and relevance classification.
3. Backend/rules verify classification and missing fields.
4. Manager decides keep, skip, needs_review, or blocked_irrelevant.
5. Kept tender can create request/task context; skipped tender remains audited.
6. Tender deadlines feed notifications/SLA and analytics.

### Flow F: Documents, Communication, Notifications, Analytics

1. Request/quote/supplier/tender entities create document and chat contexts.
2. Internal messages and attachments remain internal unless explicitly published through document center.
3. Reminders and SLA alerts target entities but reveal only permitted content.
4. Analytics aggregate from audited workflow events after core implementation exists.

## 17. Gaps And Open Decisions

| Gap or decision | Why it matters | Recommended owner/task |
| --- | --- | --- |
| Permission matrix | Prevents accidental over-permissioning and frontend-only auth | Security/RBAC implementation readiness. |
| Audit event taxonomy | Required for agents, permissions, quote, supplier, document, and matcher decisions | Security/audit foundation. |
| Request state machine | Staff workspace, SLA, notifications, analytics, and quote flow depend on it | CRM workflow foundation. |
| Quote state machine and approvals | Needed before KP/PDF generation and customer-facing commercial flow | Commercial workflow foundation. |
| Supplier quote MVP scope | Determines manual registration vs mail parsing/API | Supplier workflow foundation. |
| Document storage and scanning | Required before attachments and customer-visible documents | Document service foundation. |
| Product Selector evaluation runner | Needed before trusting model output quality | Agent quality task. |
| Catalog import file formats | Needed before parser/import implementation | Catalog import task. |
| Price/discount policy | Needed before quote totals and margin-sensitive actions | Pricing policy task. |
| Delivery estimate rules | Needed before customer-facing delivery labels | Delivery service task. |
| Notification/SLA runtime rules | Needed before reminders/escalations | Notification/SLA task. |
| Customer organization MVP boundary | Prevents overbuilding organization sharing too early | Product scope decision. |
| Tender evaluation fixtures | Needed before tender automation beyond candidate extraction | Tender quality task. |
| 1C integration boundary | Required before final document/accounting handoff | Integration architecture task. |

## 18. Risk Register

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Too much scope in first implementation | Slow delivery and fragile architecture | High | Define strict MVP slices and postpone advanced features. |
| LLM output treated as truth | Wrong products, prices, documents, or decisions | Medium | Enforce backend validation and manager review. |
| RBAC implemented too late | Sensitive data leakage and rework | High | Build permission/audit foundation before business workflows. |
| Universal catalog parser | Wrong matches across product types | Medium | Use product-type-specific parsing/filter profiles. |
| Quote generation before price policy | Incorrect customer-facing commercial documents | Medium | Freeze pricing, approval, and snapshot rules first. |
| Supplier response silently updates customer data | Commercial errors and audit gaps | Medium | Require explicit apply actions with permissions. |
| Document visibility leakage | Customer sees internal/supplier/commercial files | Medium | Build document visibility and publication boundary early. |
| Notification noise | Staff ignores important alerts | Medium | Add severity, preferences, digest, mute, and anti-spam rules. |
| Analytics before reliable events | Misleading dashboards | Medium | Implement event/audit foundation before dashboards. |
| Tender automation overreach | Bad keep/skip decisions or compliance risks | Medium | Keep Tender Reader as candidate data and manager-reviewed. |
| 1C integration too early | Expensive rework and bad handoff data | Medium | Implement after quote/document data is stable. |
| Customer organization sharing too early | Ownership/security complexity | Medium | Keep own-only MVP first. |

## 19. Prioritized Implementation Roadmap

### Phase 0: Implementation Readiness Gate

- Permission matrix and audit taxonomy.
- Request/position lifecycle state machine.
- Quote/supplier/document state machines.
- API contract hardening for MVP endpoints.
- MVP scope confirmation.

### Phase 1: Backend Foundation

- Authentication and authorization enforcement skeleton.
- Core entity persistence for request cards and positions.
- Audit/event foundation.
- Backend service boundaries for catalog, matcher, supplier quote, quote, documents, notifications.
- No customer-facing marketplace complexity yet.

### Phase 2: Catalog And Matcher MVP

- ROSMA catalog import profile.
- Product-type-specific parser/filter profiles.
- Catalog item publication/versioning baseline.
- Backend Catalog Matcher implementation.
- Product Selector validation and AgentRun storage.
- Manual manager review flow.

### Phase 3: Staff Request Workflow MVP

- Staff workspace request inbox and assignment.
- Request card/position review.
- Product selection review and matcher result handling.
- Manual supplier quote request/response registration.
- Basic reminders and SLA flags.

### Phase 4: Commercial Offer MVP

- KP draft lifecycle.
- Quote line snapshots.
- Basic approval rules.
- Backend PDF/Excel generation from confirmed data.
- Customer-visible document publication.
- Future 1C payload design, not full integration unless separately scoped.

### Phase 5: Customer Marketplace MVP

- Public catalog browsing and product cards.
- Authentication before add-to-cart.
- Customer-owned cart/request creation.
- Own-only customer history.
- No organization sharing unless explicitly prioritized.

### Phase 6: Expansion

- Customer organization sharing.
- Advanced notifications/SLA runtime.
- Analytics dashboards.
- Tender evaluation and automation support.
- Document scanning/OCR/parsing.
- Multi-manufacturer product selector adapters.
- 1C integration.

## 20. Recommended Service Improvements

| Improvement | Why useful | Priority | Dependency |
| --- | --- | --- | --- |
| Permission Decision Service | Centralizes RBAC and object ownership checks | Critical | Security/RBAC matrix. |
| Audit/Event Service | Feeds traceability, analytics, agent QA, and compliance | Critical | Event taxonomy. |
| Workflow State Machine Service | Prevents invalid request/quote/supplier/document transitions | Critical | Lifecycle definitions. |
| Agent Validation Service | Converts candidate data into accepted/rejected/review states | Critical | Agent JSON schemas and error taxonomy. |
| Catalog Import Profile Registry | Keeps manufacturer/product-type parsing maintainable | High | Catalog source mapping. |
| Matcher Execution Recorder | Makes match decisions explainable and auditable | High | Catalog Matcher implementation. |
| Supplier Quote Registry | Controls supplier request/response lifecycle and sensitive data | High | Supplier workflow MVP. |
| Document Visibility Gateway | Prevents accidental leakage of internal files | High | Document Center implementation. |
| Quote Snapshot Generator | Guarantees reproducible customer-facing KP versions | High | Commercial lifecycle. |
| Notification Routing Service | Keeps operational signals permission-aware | Medium | Workflow and permissions. |
| Search/Index Boundary | Supports catalog, request, document, and messenger search safely | Medium | Data model and permissions. |
| Evaluation Runner | Measures Product Selector/Tender Reader quality before integration | Medium | Fixture sets. |

## 21. Codex Independent Improvement Suggestions

Suggested missing or under-specified services:

- Permission Decision Service should be explicit rather than scattered across route handlers.
- Audit/Event Service should be created before analytics and before high-risk business actions.
- Workflow State Machine Service should own allowed transitions and transition audit.
- Document Visibility Gateway should guard downloads, previews, publication, and customer portal links.
- Search/Index Boundary should be planned before indexing internal chats, files, customer data, and commercial fields.
- Prompt/Model Registry should track `prompt_version`, `model_name`, evaluation status, and rollout status.

Boundaries to strengthen before coding:

- API responses must mask sensitive fields by permission, not by frontend hiding.
- Service/system actors must have explicit permission scopes.
- All LLM and parser outputs must carry source fragments, confidence, warnings, and validation status.
- Quote generation must depend on confirmed catalog/price/delivery data, not on free-text agent output.
- Document publication must be a deliberate backend action.

Risk-reducing implementation order:

1. Build permission/audit foundations.
2. Implement request and position MVP.
3. Implement catalog import and matcher MVP.
4. Implement staff review workflow.
5. Implement supplier quote and KP workflows.
6. Add customer portal and analytics after reliable backend data exists.

MVP simplification recommendation:

- Start with staff-side request processing, ROSMA catalog import, Product Selector validation, Backend Catalog Matcher, manual supplier quote registration, and KP draft lifecycle.
- Keep customer marketplace public browsing minimal at first.
- Keep customer accounts own-only.
- Keep Tender Reader as candidate review, not automation.
- Keep analytics limited to simple operational counts until audit/event data stabilizes.

Recommended postponements:

- Customer organization sharing.
- Advanced marketplace comparison/favorites/repeat request UX.
- OCR/parsing of uploaded files.
- Full realtime messenger and scheduled messages.
- Automated supplier mailbox/API integration.
- 1C integration.
- Full BI dashboards and sensitive exports.
- Multi-manufacturer Product Selector adapters beyond ROSMA.

## 22. Final Verdict

ArtCRM architecture is ready for the next planning step, but not for unconstrained business implementation.

Recommended status: partially ready / ready for controlled MVP implementation planning.

The architecture correctly establishes the most important strategic boundaries:

- LLM agents are candidate-data producers.
- Backend services own validation, decisions, integrations, secrets, and persistence.
- Catalog Matcher is a backend-only decision service.
- KP/PDF/invoice generation is backend template/generator work based on confirmed data.
- Security, permissions, audit, and visibility must be backend-enforced.
- Customer, staff, service actor, document, chat, supplier, and commercial data boundaries are separate.

Top five required tasks before business coding:

1. Permission matrix and audit/event taxonomy.
2. Request/position state machine and MVP API contracts.
3. Quote/supplier/document state machines and transition guards.
4. Catalog import and Backend Catalog Matcher implementation plan with acceptance criteria.
5. MVP scope decision separating staff-side first release from future marketplace/analytics/tender expansion.

Top five optional but valuable tasks before larger rollout:

1. Product Selector automated evaluation runner.
2. Tender Reader evaluation fixtures.
3. Document storage/scanning/publication architecture deep dive.
4. Search/index permission boundary design.
5. Customer organization sharing policy and data ownership model.

Final recommendation: proceed with a small, backend-first MVP implementation plan after this review, beginning with security/audit/workflow foundations and avoiding broad UI, marketplace, analytics, 1C, and automation work until core data quality and permissions are stable.

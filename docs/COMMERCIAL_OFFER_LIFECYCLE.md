# Commercial Offer Lifecycle

This document defines the documentation-only architecture for ArtCRM commercial offer / КП lifecycle, quote versioning, approval boundaries, commercial data visibility, and audit.

It does not implement frontend UI, backend APIs, pricing engine, approval engine, quote PDF/Excel generation, email sending, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real prices, real discounts, real customer data, credentials, tokens, secrets, or business logic.

## Purpose

A commercial offer / КП is a central commercial object between customer cart/request, catalog matching, validated prices, discounts, margins, supplier quote responses, approval, documents, and customer communication.

КП must be separate from a cart and a request:

- cart represents customer selection intent;
- request represents CRM processing work;
- quote represents a versioned commercial proposal that can be approved, sent, accepted, rejected, expired, or revised;
- quote must preserve customer-facing terms as a reproducible snapshot.

КП needs versions, statuses, approval, and audit because prices, delivery, discounts, supplier responses, and customer-facing documents may change over time. Sent quotes should remain reproducible and should not silently change after delivery to the customer.

Purchase price, supplier discount, margin, manual discount reason, supplier response, and internal commercial notes are sensitive fields. Access must depend on explicit permissions, not only on role names.

## Scope

Covered here:

- quote lifecycle;
- quote versioning;
- quote lines;
- relationship to cart, request, catalog item, and matcher result;
- price fields and sensitive visibility;
- manual discounts;
- approval boundaries;
- director approval;
- customer-facing vs internal fields;
- quote export PDF/Excel as future boundary;
- relationship to Response Draft Agent;
- audit and activity timeline.

Not covered here:

- pricing engine implementation;
- quote PDF generation;
- Excel generation;
- email sending;
- approval engine implementation;
- database schema;
- backend APIs;
- frontend UI;
- real prices or discounts.

## Commercial Data And Flexible Permissions

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can be granted additional commercial, document, or supplier permissions if company policy allows.
- Manager can receive selected Director-level approval, export, or margin functions if explicitly granted.
- Manager Assistant can receive the same commercial workflow functions as Manager or selected elevated functions if explicitly granted.
- Administrator does not automatically see purchase prices, supplier discounts, margins, supplier responses, or commercial documents unless permission allows it.
- Director can have commercial overview but may lack operational edit/send actions unless explicitly granted.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive commercial capabilities require explicit permissions:

- view purchase price;
- view supplier discount;
- view margin;
- apply manual discount;
- approve discount;
- override price;
- send quote to customer;
- export quote;
- export sensitive commercial data;
- view supplier quote response;
- apply supplier price update;
- apply supplier delivery update;
- download internal commercial document;
- publish customer-visible document;
- delete document;
- view audit.

This principle extends [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md). No permission engine is implemented in this task.

## Quote Lifecycle

Conceptual quote statuses:

- `draft`;
- `internal_review`;
- `awaiting_approval`;
- `approved`;
- `sent`;
- `accepted`;
- `rejected`;
- `expired`;
- `canceled`;
- `archived`.

Lifecycle rules:

- statuses are conceptual;
- exact workflow state machine is deferred;
- status transitions require permissions;
- status transitions must be auditable;
- customer-facing status may differ from internal status;
- sent quote should be immutable or versioned after sending;
- quote changes after sending should create a new version or revision;
- a quote can be canceled or archived without deleting audit history.

Possible conceptual transitions:

- `draft` -> `internal_review` when manager requests review;
- `internal_review` -> `awaiting_approval` when discount/margin/override policy requires approval;
- `awaiting_approval` -> `approved` when authorized approver approves;
- `awaiting_approval` -> `draft` or `internal_review` when rejected for revision;
- `approved` -> `sent` when authorized user sends or exports customer-facing quote;
- `sent` -> `accepted` or `rejected` based on customer outcome;
- `sent` -> `expired` after validity period;
- any active internal status -> `canceled` when abandoned by authorized user;
- terminal statuses -> `archived` according to retention policy.

## Quote Versioning

Versioning rules:

- every major edit may create a new quote version;
- sent quotes should preserve a snapshot;
- price, discount, delivery, or line changes after sending should create a new version or revision;
- customer-visible quote must be reproducible from the version snapshot;
- internal notes must not leak to the customer version;
- exported PDF/Excel documents should reference the quote version used to generate them;
- old versions remain auditable and should not be overwritten silently.

Conceptual fields:

- `quote_id`;
- `quote_version_id`;
- `version_number`;
- `status`;
- `created_by_ref`;
- `approved_by_ref`;
- `sent_by_ref`;
- `created_at`;
- `approved_at`;
- `sent_at`;
- `valid_until`;
- `source_request_ref`;
- `source_cart_ref`;
- `audit_ref`.

No database schema or persistence implementation is added.

## Quote Line Model

Conceptual quote line fields:

- `quote_line_id`;
- `quote_id`;
- `source_request_position_ref`;
- `catalog_item_ref`;
- `matcher_execution_ref`;
- `supplier_quote_response_item_ref`;
- `display_name_customer`;
- `display_name_internal`;
- `quantity`;
- `unit`;
- `customer_price`;
- `purchase_price`;
- `supplier_discount`;
- `manual_discount`;
- `margin`;
- `delivery_estimate_customer`;
- `delivery_estimate_internal`;
- `related_component_refs`;
- `service_position_refs`;
- `line_status`;
- `audit_ref`.

Rules:

- customer-facing line must not expose purchase price, supplier discount, or margin;
- internal line may show sensitive fields only if permission allows;
- prices and delivery estimates must be snapshotted for quote version;
- line can reference service positions such as hydrofilling;
- line can reference related components validated by backend workflows;
- line should keep source links to request position, matcher result, and supplier response where available;
- line edit history must be auditable.

## Relationship To Cart, Request, Catalog, And Matcher

Conceptual relationships:

- customer cart can create a request or quote request;
- request contains request positions;
- quote line can reference a request position;
- quote line can reference a validated catalog item;
- quote line can reference Backend Catalog Matcher execution;
- quote line can reference a supplier quote response item;
- quote version snapshots customer-facing display data and commercial values.

Rules:

- Product Selector output remains candidate data and cannot directly approve a quote line;
- Backend Catalog Matcher can propose/validate catalog match decisions before quote line use;
- supplier response can support internal price and delivery data;
- quote must not expose matcher audit or supplier internals to the customer.

## Price And Discount Boundaries

Commercial fields:

- customer price;
- purchase price;
- supplier discount;
- manual customer discount;
- margin;
- delivery estimate;
- supplier confirmed delivery;
- quote validity period.

Rules:

- purchase price is sensitive;
- supplier discount is sensitive;
- margin is sensitive;
- manual discount requires permission;
- discount above threshold may require approval;
- price override requires permission;
- director approval is required for sensitive discount/margin cases if policy requires it;
- exact thresholds are deferred;
- pricing engine is not implemented;
- customer-facing quote must not include internal commercial fields.

Suggested permissions:

- `quote.view`;
- `quote.create_draft`;
- `quote.edit`;
- `quote.view_purchase_price`;
- `quote.view_supplier_discount`;
- `quote.view_margin`;
- `quote.apply_manual_discount`;
- `quote.override_price`;
- `quote.request_approval`;
- `quote.approve`;
- `quote.reject_approval`;
- `quote.send_to_customer`;
- `quote.export`;
- `quote.export_sensitive`;
- `quote.cancel`;
- `quote.archive`.

## Approval Boundaries

Approval may be required for:

- manual discount;
- low margin;
- price override;
- strategic customer;
- non-standard delivery or commercial terms;
- quote sending before customer delivery;
- publishing customer-visible quote documents.

Director approval:

- Director may approve sensitive discounts and margins if permission allows;
- Manager may receive approval permission if company policy allows;
- Manager Assistant may receive approval-support permissions if explicitly granted;
- Administrator does not automatically approve commercial decisions;
- approver permissions are explicit, not role-name-only.

No approval engine, workflow runtime, thresholds, or UI are implemented.

## Customer-Facing Vs Internal Quote Fields

Customer-facing fields may include:

- quote number;
- customer company/contact;
- product names;
- product public descriptions;
- quantity;
- unit;
- customer price;
- delivery estimate;
- validity period;
- terms;
- public documents;
- manager contact.

Internal-only fields include:

- purchase price;
- supplier discount;
- margin;
- internal notes;
- supplier quote response;
- matcher audit;
- manual discount reason;
- approval trail;
- staff comments;
- internal files;
- internal delivery assumptions;
- pricing calculation notes.

Rules:

- customer-facing fields must be produced from the quote version snapshot;
- internal fields must not leak into PDF/Excel/customer message;
- visibility must be enforced by backend permissions later.

## Quote Export Boundary

Future export concepts:

- PDF export;
- Excel export;
- customer-facing commercial offer document;
- internal commercial export;
- sensitive analytics/commercial export.

Rules:

- export must use quote version snapshot;
- customer-facing export must not include internal fields;
- sensitive export requires elevated permission;
- export action must be audited;
- exported document should be registered in [CRM Document Center](CRM_DOCUMENT_CENTER.md) later;
- PDF/Excel generation is not implemented in this task.

## Response Draft Agent Relationship

Response Draft Agent may draft an email or customer message based on approved quote/customer-facing data.

Rules:

- Response Draft Agent may use approved customer-facing quote fields;
- Response Draft Agent output is a draft only;
- Response Draft Agent must not calculate sums, VAT, prices, discounts, margins, requisites, totals, or final PDF content;
- Response Draft Agent must not access purchase price, supplier discount, margin, or internal notes unless workflow and permissions explicitly allow it;
- sending requires explicit user action and permission;
- generated content must be auditable;
- backend validation remains mandatory before any generated content is used.

## Activity Timeline And Audit

Future audit events:

- quote draft created;
- quote version created;
- quote line added;
- quote line removed;
- quote line changed;
- catalog item changed;
- matcher result linked;
- supplier response linked;
- manual discount applied;
- price override applied;
- approval requested;
- quote approved;
- quote rejected;
- quote sent;
- quote accepted by customer;
- quote rejected by customer;
- quote expired;
- quote canceled;
- quote exported;
- customer-facing document generated;
- sensitive field viewed;
- sensitive export created;
- access denied to commercial data.

Audit events should capture actor, timestamp, quote/version/line, previous and new state when relevant, permission used, reason/comment when available, and source service/agent where relevant.

## Relationship To Other Docs

Related documents:

- [Staff Workspace And Request Pipeline](STAFF_WORKSPACE_AND_PIPELINE.md)
- [Customer Marketplace Portal](CUSTOMER_MARKETPLACE_PORTAL.md)
- [Customer Organization Access](CUSTOMER_ORGANIZATION_ACCESS.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)
- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Supplier Quote Workflow](SUPPLIER_QUOTE_WORKFLOW.md)
- [CRM Document Center](CRM_DOCUMENT_CENTER.md)
- [Agent Platform](AGENT_PLATFORM.md)

## Deferred Implementation

Explicitly deferred:

- pricing engine;
- approval engine;
- PDF generation;
- Excel generation;
- email sending;
- frontend UI;
- backend APIs;
- database schema;
- SQL;
- ORM;
- migrations;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- real prices;
- real discounts;
- real customer data;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-QUOTE-001

This task does not add:

- commercial offer UI;
- quote API;
- price calculation;
- discount calculation;
- VAT/tax calculation;
- quote approval runtime;
- quote PDF/Excel generator;
- email delivery;
- document generation;
- database tables;
- production data.

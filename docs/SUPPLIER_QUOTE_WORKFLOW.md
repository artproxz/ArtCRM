# Supplier Quote Workflow

This document defines the documentation-only architecture for supplier quote request and response workflow in ArtCRM, with ROSMA as an initial important supplier scenario.

It does not implement email sending, mailbox parsing, supplier API integrations, backend services, frontend UI, pricing engine, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real supplier data, real prices, credentials, tokens, secrets, or business logic.

## Purpose

Managers need a controlled way to request exact prices, availability, delivery terms, and service-position details from ROSMA or other suppliers. A future action such as "Request exact information from ROSMA" should create a reviewed supplier quote request draft rather than sending untracked messages.

Supplier responses can affect request, cart, quote, and document context. Because supplier price, supplier discount, delivery terms, and supplier comments are sensitive commercial data, responses must be registered, applied, and audited through controlled backend workflows later.

Supplier quote workflow connects:

- customer request or marketplace cart;
- request positions and service positions;
- Backend Catalog Matcher result;
- commercial offer / КП lifecycle;
- supplier documents and attachments;
- staff workspace waiting supplier state;
- notifications and SLA pauses;
- permissions and audit.

## Scope

Covered here:

- supplier quote request lifecycle;
- request draft generation;
- line items in supplier request;
- hydrofilling and service positions;
- email sending boundary;
- response registration;
- delivery update application;
- price update application;
- relationship to cart, request, quote, customer, and supplier;
- relationship to document center;
- audit;
- permissions;
- sensitive commercial data.

Not covered here:

- email sending;
- mailbox parsing;
- supplier API integrations;
- backend implementation;
- database schema;
- frontend UI;
- price calculation engine;
- real supplier data.

## Commercial Data And Flexible Permissions

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can be granted additional commercial, document, or supplier permissions if company policy allows.
- Manager can receive selected Director-level approval, export, margin, or supplier-response functions if explicitly granted.
- Manager Assistant can receive the same supplier quote workflow functions as Manager or selected elevated functions if explicitly granted.
- Administrator does not automatically see purchase prices, supplier discounts, margins, supplier responses, or commercial documents unless permission allows it.
- Director can have commercial overview but may lack operational edit/send/apply actions unless explicitly granted.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive supplier/commercial capabilities require explicit permissions:

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

## Supplier Quote Request Lifecycle

Conceptual statuses:

- `draft`;
- `ready_to_send`;
- `sent`;
- `waiting_response`;
- `response_received`;
- `partially_answered`;
- `applied`;
- `canceled`;
- `expired`;
- `archived`.

Lifecycle rules:

- lifecycle is conceptual;
- exact state machine is deferred;
- sending is a future boundary;
- response parsing is a future boundary;
- manual response registration may be a future workflow;
- all status changes must be audited;
- supplier response should not silently update request, quote, or customer-facing fields;
- applying response data requires explicit permission.

## Supplier Request Draft

Supplier request draft is a future object prepared for manager review before any sending.

Conceptual fields:

- `supplier_quote_request_id`;
- `supplier_ref`;
- `supplier_contact_ref`;
- `source_request_ref`;
- `source_cart_ref`;
- `source_quote_ref`;
- `created_by_ref`;
- `status`;
- `subject`;
- `message_body`;
- `line_items[]`;
- `created_at`;
- `sent_at`;
- `response_due_at`;
- `audit_ref`.

Line item fields:

- `supplier_quote_request_item_id`;
- `catalog_item_ref`;
- `article`;
- `display_name`;
- `quantity`;
- `unit`;
- `customer_request_position_ref`;
- `comment`;
- `service_position_refs`;
- `needs_price_confirmation`;
- `needs_delivery_confirmation`;
- `needs_availability_confirmation`.

Rules:

- draft generation should use validated catalog/request data when implemented later;
- Product Selector output remains candidate data and cannot directly create a supplier request without backend validation;
- manager must review supplier request draft before sending if future implementation allows sending;
- no supplier email credentials are stored or used here;
- no real supplier data is included.

## Draft Message Content

Example future draft text with placeholders only:

```text
Добрый день!

Запрашиваем КП на следующие позиции:

1) [артикул] / [полное наименование] / [количество]
2) [артикул] / [полное наименование] / [количество]

Дополнительно:
- [гидрозаполнение / услуга / комментарий при наличии]

Просьба указать цену, наличие и ориентировочный срок поставки.
```

Rules:

- no real supplier emails;
- no sending implementation;
- no credentials;
- message body is draft only;
- manager must review before sending if future implementation allows;
- message draft must not expose customer-private information unless supplier workflow and permissions allow it.

## Hydrofilling And Service Positions

Hydrofilling may be represented as a service position linked to a parent item.

Rules:

- service positions must be included in supplier quote request when relevant;
- examples include hydrofilling with silicone or glycerin for compatible series;
- hydrofilling remains a separate service-position concept, not only a note inside the main item;
- no automatic unsupported hydrofilling assumptions;
- unsupported service requests require review;
- service positions may affect price and delivery;
- parent product compatibility must be checked by backend validation later;
- supplier response can confirm or reject service feasibility.

Conceptual service-position line details:

- `service_type` such as `hydrofilling`;
- `parent_position_ref`;
- `parent_catalog_item_ref`;
- `fluid_type` if provided;
- `quantity_policy` such as `same_as_parent`;
- `quantity`;
- `requires_confirmation`;
- `backend_validation_required`;
- `supplier_confirmation_status`.

## Supplier Response Registration

Supplier response may be registered manually in a future workflow. Future mailbox parsing and supplier API integrations are deferred.

Supplier response may include:

- confirmed price;
- discount;
- availability;
- delivery date / delivery estimate;
- replacement or analog suggestion;
- comments;
- attached documents;
- validity period.

Conceptual response fields:

- `supplier_quote_response_id`;
- `supplier_quote_request_ref`;
- `received_at`;
- `registered_by_ref`;
- `response_source`;
- `response_items[]`;
- `attachments[]`;
- `status`;
- `audit_ref`.

Response item fields:

- `supplier_quote_response_item_id`;
- `supplier_quote_request_item_ref`;
- `confirmed_price`;
- `confirmed_discount`;
- `confirmed_delivery`;
- `availability_status`;
- `supplier_comment`;
- `suggested_replacement`;
- `valid_until`;
- `apply_status`.

No real prices, discounts, supplier names, supplier contacts, or customer data are included in this documentation.

## Applying Price And Delivery Updates

Applying supplier response data is a controlled future workflow.

Rules:

- applying supplier price update requires permission;
- applying supplier delivery update requires permission;
- applying response to quote line must be audited;
- supplier response should not silently overwrite customer-facing quote after it has been sent;
- if quote was already sent, supplier update may require a new quote version;
- if price or delivery changed, related quote/cart/request should show `needs_review`;
- supplier replacement/analog suggestions require validation before use;
- supplier comments remain internal unless explicitly converted into customer-facing terms.

Suggested permissions:

- `supplier_quote.create_request`;
- `supplier_quote.edit_request`;
- `supplier_quote.send_request`;
- `supplier_quote.view_response`;
- `supplier_quote.register_response`;
- `supplier_quote.apply_price_update`;
- `supplier_quote.apply_delivery_update`;
- `supplier_quote.link_attachment`;
- `supplier_quote.cancel`;
- `supplier_quote.archive`;
- `supplier_quote.view_sensitive_terms`.

## Supplier Data Sensitivity

Sensitive supplier data:

- supplier price;
- supplier discount;
- supplier delivery terms before customer publication;
- supplier comments;
- supplier quote documents;
- replacement/analog suggestions;
- internal response notes;
- supplier contact details if not customer-visible.

Rules:

- customer should not see supplier response directly;
- customer-facing quote fields must be created separately from supplier response;
- supplier quote documents are internal unless explicitly published or transformed into customer-visible documents;
- commercial-sensitive data requires explicit permission;
- Administrator does not automatically see supplier terms unless permission allows it;
- Director can view commercial overview if permission allows, but operational apply/send actions are separate permissions.

## Relationship To Quote Lifecycle

Supplier response can support [Commercial Offer Lifecycle](COMMERCIAL_OFFER_LIFECYCLE.md).

Rules:

- supplier response can support quote draft;
- supplier response may update purchase price;
- supplier response may update delivery estimate;
- quote version should snapshot applied supplier data;
- quote sent to customer should not expose supplier internals;
- quote revision may be needed after supplier update;
- quote approval may be required if supplier update changes margin or discount risk.

## Relationship To Document Center

Supplier responses may include attachments.

Rules:

- attachments should be stored/linked in [CRM Document Center](CRM_DOCUMENT_CENTER.md) later;
- supplier documents may be internal-only;
- public/customer-visible documents require explicit publish decision;
- document visibility must be permission-controlled;
- scanning, OCR, parsing, preview, upload, and download are deferred.

## Relationship To Staff Workspace And Notifications

Supplier quote workflow should connect to [Staff Workspace And Request Pipeline](STAFF_WORKSPACE_AND_PIPELINE.md) and [Notifications, Reminders And SLA Alerts](NOTIFICATIONS_REMINDERS_SLA.md).

Concepts:

- supplier quote request appears in staff workspace;
- request can enter `waiting_supplier` state;
- supplier response received can create manager notification;
- supplier overdue can create alert;
- manager attention queue can surface response_received / partially_answered states;
- SLA may pause while waiting supplier if policy allows;
- SLA pause and resume must be audited.

## Relationship To Cart, Request, Customer, And Supplier

Conceptual relationships:

- supplier request may originate from customer request, cart, quote, or request position;
- supplier request line references catalog item or validated candidate;
- supplier response can affect internal commercial data for quote preparation;
- customer organization/request context is used only as needed and must respect privacy;
- supplier response should not create customer-visible communication by itself.

## Audit Events

Future audit events:

- supplier quote request draft created;
- supplier quote request item added;
- supplier quote request item removed;
- supplier quote request marked ready;
- supplier quote request sent;
- request moved to waiting supplier;
- response received;
- response registered;
- partial response registered;
- price update applied;
- delivery update applied;
- availability update applied;
- replacement suggestion recorded;
- attachment linked;
- request canceled;
- supplier request expired;
- sensitive supplier data viewed;
- access denied to supplier data.

Audit records should capture actor, timestamp, target request/response/item, previous and new state where relevant, permission used, supplier reference, and source channel if available.

## Deferred Implementation

Explicitly deferred:

- email sending;
- mailbox parsing;
- supplier API integration;
- backend services;
- frontend UI;
- price engine;
- approval engine;
- file upload/download;
- document preview;
- database schema;
- SQL;
- ORM;
- migrations;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- real supplier data;
- real prices;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-SUPPLIER-001

This task does not add:

- supplier email integration;
- supplier API client;
- mailbox parser;
- response parser;
- price update code;
- delivery update code;
- supplier request UI;
- database tables;
- real supplier contacts;
- real commercial values.

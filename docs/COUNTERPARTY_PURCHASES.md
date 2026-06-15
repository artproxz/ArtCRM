# Counterparty Purchases Architecture

This document defines the documentation-only architecture for purchase records linked to counterparties in ArtCRM.

It does not implement backend code, frontend code, purchase service, API routes, database schema, SQL, ORM, migrations, UI, 1C integration, tests, dependencies, containers, `.env.example` changes, real customer/counterparty data, real prices, credentials, tokens, secrets, or business logic.

## Purpose

A purchase is an internal procurement/commercial execution object linked to a counterparty and, later, possibly to a customer organization. It is separate from:

- request;
- cart;
- quote;
- quote version;
- supplier quote request;
- supplier quote response.

Purchase records help staff track internal procurement or fulfillment context after manager review. A purchase may be influenced by an accepted quote, supplier response, customer request, or future accounting handoff, but it must not be silently created by those objects.

## Separation Rules

- Request describes CRM work and customer need.
- Cart describes customer selection intent.
- Quote/KP describes customer-facing commercial proposal.
- QuoteVersion preserves a reproducible sent snapshot.
- SupplierQuoteRequest asks supplier for price/availability/delivery.
- SupplierQuoteResponse records supplier-provided internal commercial data.
- Purchase records internal procurement/execution status and sensitive commercial context.

Supplier response can support purchase context later but cannot create a confirmed purchase silently. Purchase lifecycle transitions are governed by the `Purchase` state machine.

## Purchase Creation Sources

Future purchase draft sources may include:

- manual creation from counterparty profile;
- accepted quote;
- customer request;
- marketplace cart after manager review;
- supplier quote response after manager review;
- future 1C/accounting handoff;
- future import.

All sources create reviewable purchase draft context only. Approval, ordering, and receiving remain controlled by purchase state transitions and permissions.

## Purchase Fields

Conceptual fields:

- purchase ID;
- counterparty ref;
- customer organization ref;
- responsible manager;
- assistant;
- source request ref;
- source quote ref;
- supplier quote refs;
- status;
- purchase lines;
- customer-visible status if any;
- internal status;
- documents;
- internal comments;
- audit refs;
- created date;
- updated date.

No database schema is created. These fields are implementation-readiness concepts only.

## Purchase Lines

A purchase line should link to relevant source/context objects where available:

- catalog item;
- quote line;
- request position;
- service position;
- supplier quote response;
- stock snapshot where applicable;
- price snapshot where applicable.

Line concepts:

- line ref;
- product/service display name;
- quantity;
- unit;
- internal status;
- source quote line ref;
- source request position ref;
- catalog item ref;
- supplier response item ref;
- service position ref;
- stock/price snapshot refs;
- sensitive price fields when allowed;
- document refs;
- audit refs.

Purchase lines must not expose supplier price, purchase price, supplier discount, margin, or supplier docs unless permissions allow it.

## Purchase Lifecycle

Use states from `docs/MVP_STATE_MACHINES.md`:

- `draft`;
- `internal_review`;
- `approved`;
- `ordered`;
- `partially_received`;
- `received`;
- `canceled`;
- `archived`.

Conceptual transition rules:

- `draft` -> `internal_review` uses `purchase.create` / `purchase.update`.
- `internal_review` -> `approved` uses `purchase.approve`.
- `approved` -> `ordered` uses `purchase.update`.
- `ordered` -> `partially_received` uses `purchase.update`.
- `partially_received` -> `received` uses `purchase.update`.
- active state -> `canceled` uses `purchase.update` and requires reason.
- terminal state -> `archived` preserves audit history.

Purchase creation/update/approval is commercial-sensitive and auditable.

## Purchase Actions

Future manager actions:

- create purchase draft;
- update draft;
- send to review;
- approve purchase;
- order;
- register partial receipt;
- register receipt;
- cancel with reason;
- attach documents;
- link supplier response;
- link quote/request;
- view audit.

Action boundaries:

| Action | Permission |
| --- | --- |
| View purchase | `purchase.view` |
| Create draft | `purchase.create` |
| Update draft/status details | `purchase.update` |
| Approve purchase | `purchase.approve` |
| Export purchase data | `purchase.export` |
| View purchase price | `pricing.view_purchase_price` |
| View supplier discount | `pricing.view_supplier_discount` |
| View margin | `pricing.view_margin` |
| View supplier response context | `supplier_quote.view_response` |
| View internal documents | `documents.view_internal` |
| View audit | `audit.view` |

No new permission names are introduced by this document.

## Search And Filter Purchases

Future purchase list/profile filters:

- counterparty;
- responsible manager;
- status;
- date;
- has supplier quote;
- waiting supplier;
- delivery status;
- source quote;
- source request;
- document status;
- archived/canceled/active.

Search and filtering must be backend-permission-aware. Sensitive commercial fields must be masked in lists unless the viewer has matching permissions.

## Sensitive Fields

Purchase may contain:

- supplier price;
- purchase price;
- supplier discount;
- internal margin;
- internal comments;
- supplier documents;
- supplier response references;
- commercial-sensitive documents;
- internal approval reasons.

Rules:

- `pricing.view_purchase_price` is required for purchase price.
- `pricing.view_supplier_discount` is required for supplier discount.
- `pricing.view_margin` is required for margin.
- `supplier_quote.view_response` is required for supplier response details.
- `documents.view_internal` is required for internal documents.
- Sensitive views and exports must be audited.
- Customer-facing status, if any, must be safe and not expose internal procurement terms.

## Relationship To Counterparty Profile

A counterparty profile may show:

- linked purchases count;
- active purchases;
- purchase statuses;
- last purchase activity;
- purchase documents when permitted;
- audit timeline entries;
- create purchase draft action.

The profile does not bypass purchase permissions. Opening or creating purchase records must go through backend permission checks and future purchase state guards.

## Relationship To Requests, Quotes, Supplier Quotes, Documents, And Chats

- Request can be a source context for purchase draft.
- Accepted quote can be a source context, but quote acceptance does not automatically create confirmed purchase.
- Supplier quote response can support price/delivery/availability context after manager review.
- Documents linked to purchase follow Document Center visibility and audit rules.
- Internal chats linked to purchase are staff-only and require messenger/entity permissions.
- Analytics may later use purchase state and sensitive fields only with permissions.

## Future 1C Boundary

1C handoff is a future integration.

Rules:

- purchase may later become source data for 1C documents;
- 1C runtime is not implemented here;
- backend owns mapping, validation, idempotency, retry, and audit;
- no direct frontend access to 1C;
- no 1C credentials, tokens, endpoints, or document payloads are documented here;
- purchase state and approved data should be stable before any 1C integration task.

## Audit Events

Use existing taxonomy where applicable:

- `purchase.created`;
- `purchase.updated` or `purchase.state_changed` when future taxonomy expands;
- `purchase.approved`;
- `purchase.ordered`;
- `purchase.partially_received`;
- `purchase.received`;
- `purchase.canceled`;
- `purchase.archived`;
- sensitive field viewed events for purchase price, supplier discount, and margin;
- document viewed/downloaded events for linked internal documents.

Audit metadata should include safe refs, state changes, permission used, actor, reason, idempotency key where applicable, and source request/quote/supplier refs. It must not include secrets, raw supplier documents, unrestricted commercial details, or customer data dumps.

## Explicitly Not Implemented

This task does not add:

- purchase service;
- purchase API;
- purchase UI;
- database schema;
- SQL;
- ORM;
- migrations;
- purchase calculations;
- supplier integration;
- 1C integration;
- file upload/download;
- document generation;
- real prices;
- real purchase records;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- credentials, tokens, secrets, or business logic.

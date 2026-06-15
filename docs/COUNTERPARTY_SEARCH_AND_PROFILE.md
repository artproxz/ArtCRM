# Counterparty Search, Filters And Profile Architecture

This document defines the documentation-only architecture for manager-facing counterparty search, filters, and profile cards in ArtCRM.

It does not implement backend code, frontend code, search service, indexes, API routes, database schema, SQL, ORM, migrations, UI, tests, dependencies, containers, `.env.example` changes, real customer/counterparty data, credentials, tokens, secrets, or business logic.

## Purpose

Managers need a clear internal registry for companies/customers imported from amoCRM, created manually later, or enriched through reviewed public information. The registry must support safe search, data quality review, links to CRM work, and controlled actions from the counterparty profile.

Counterparty search is internal CRM functionality by default. It must not leak the full customer/counterparty database to guests or customer users.

## Counterparty List

The counterparty list should show a compact, permission-filtered registry view.

Visible fields for permitted staff users may include:

- display name;
- legal name;
- INN;
- primary phone;
- primary email;
- city/region;
- responsible manager;
- source;
- customer level/tier;
- status;
- data quality flags;
- last activity;
- linked requests count;
- linked quotes count;
- linked purchases count.

Field masking applies before response serialization. Sensitive details must not appear only because the frontend hides them.

## Search

Search should be conceptually supported by:

- company name;
- legal name;
- normalized name;
- INN;
- phone;
- email;
- address;
- city/region;
- amoCRM ID;
- responsible manager;
- source;
- customer level/tier;
- contact person.

Search must use backend authorization. A broad registry search can expose the customer base and therefore requires `counterparty.search`. Export requires `counterparty.export` and audit.

## Filters

Future filters should include:

- responsible manager;
- source;
- customer level/tier;
- region/city;
- INN present/missing;
- duplicate risk;
- has open requests;
- has active quotes;
- has purchases;
- has documents;
- has internal chat;
- imported from amoCRM;
- enrichment status;
- last activity period;
- created/updated period;
- archived/suspended/active.

Filter fields must be validated by the backend. Customer-facing autocomplete or suggestions must not expose internal counterparty registry data.

## Counterparty Profile Card

The profile card is an internal CRM view of a single counterparty. It should aggregate identity, quality, relationships, and allowed actions.

Sections:

- Identity: display name, status, source refs, amoCRM ID presence, creation/update metadata.
- Legal information: legal name, INN, future KPP/OGRN fields, legal status candidates.
- Contacts: phones, emails, contact person candidates, source quality flags.
- Addresses: legal, delivery, postal, or source address candidates.
- Responsible staff: responsible manager, assistant, team/watchers if future policy allows.
- Source and level: source label, customer level/tier, imported-from flags.
- Notes: internal notes with safe display and audit rules.
- Data quality warnings: missing INN, invalid phone/email, unknown manager/source/tier, stale enrichment.
- Duplicate/merge candidates: review queue and merge decision history.
- Linked requests: active and historical request cards.
- Linked quotes: commercial offers / KP and quote versions.
- Linked purchases: purchase records and status summary.
- Linked documents: internal/customer-visible document refs according to document permissions.
- Linked messages/chats: internal entity-linked threads according to messenger permissions.
- Activity timeline: audit events, import events, updates, enrichment, merge reviews.
- Enrichment block: requested/previewed/validated/needs_review/applied/rejected/failed states.
- Audit history: permission-filtered audit records.

## Actions From Profile

All actions are future backend-controlled operations, not UI or business logic in this task.

| Action | Boundary | Permission notes |
| --- | --- | --- |
| Create request | Creates request context later. | Requires request permissions in future implementation. |
| Create purchase draft | Starts purchase draft linked to counterparty. | `purchase.create`. |
| Create quote context if allowed | Uses request/quote lifecycle, not direct customer commitment. | Quote permissions from existing architecture. |
| Open linked request | View only if actor can access target request. | Request permissions and object scope. |
| Open linked quote | View only if actor can access quote and sensitive fields. | Quote/pricing permissions and masking. |
| Open linked purchase | View purchase record. | `purchase.view`. |
| Add note | Internal counterparty update. | `counterparty.update`. |
| Update profile | Reviewed field update. | `counterparty.update`. |
| Request enrichment | Creates enrichment preview/request. | `counterparty.enrichment_request`. |
| Apply reviewed enrichment | Applies selected validated fields. | `counterparty.enrichment_apply`. |
| Review duplicate candidate | Manual merge review. | `counterparty.merge_review`. |
| Archive/suspend | Counterparty state change. | `counterparty.update`. |
| Link document | Document relationship action. | Document permissions and entity access; internal viewing uses `documents.view_internal`. |
| Open internal chat | Entity-linked internal thread. | `messenger.view_thread` plus entity access. |
| View audit | Audit history. | `audit.view` plus entity scope. |

Actions must emit audit events where they mutate state, expose sensitive data, or perform review decisions.

## Linked Entity Boundaries

Counterparty profile can link to CRM entities but must not own or bypass their workflows:

- Requests remain governed by RequestCard and RequestPosition workflows.
- Quotes/KP remain governed by quote lifecycle and quote versioning.
- Purchases remain separate from request, cart, quote, and supplier quote.
- Documents remain governed by document visibility and publication rules.
- Internal chats remain staff-only and permission-filtered.
- Supplier quote responses remain internal/commercial-sensitive.
- Future customer organization sharing is not implied by a counterparty profile.

## Customer-Facing Boundary

Important rules:

- Counterparty registry is internal CRM by default.
- Customer users must not search all counterparties.
- Guests must not search or enumerate counterparties.
- Customer users see only own account/organization data according to customer auth and future organization rules.
- Customer organization sharing is future architecture, not MVP default.
- Search suggestions, profile previews, autocomplete, analytics, and error messages must not leak the all-customer database.
- Staff support access to customer/counterparty context must be permission-checked and audited.

## Permissions

Use existing permissions:

- `counterparty.search` for registry list/search/profile visibility.
- `counterparty.update` for profile edits, archive/suspend, and reviewed corrections.
- `counterparty.merge_review` for duplicate/merge candidate review.
- `counterparty.export` for any export of search/profile results.
- `counterparty.enrichment_request` for requesting enrichment preview.
- `counterparty.enrichment_apply` for applying reviewed enrichment fields.
- `purchase.view` for linked purchase visibility.
- `purchase.create` for profile-origin purchase draft creation.
- `documents.view_internal` for internal document visibility.
- `messenger.view_thread` for linked internal chat visibility.
- `audit.view` for audit history.

No new permission names are introduced by this document.

## Search Result Safety

Search result payloads should be minimized:

- return only fields needed for the list/card;
- mask fields the actor cannot view;
- avoid returning raw notes or raw import rows;
- avoid returning supplier response or commercial-sensitive details through counters/tooltips;
- keep duplicate/enrichment details as safe summaries unless actor has review permission;
- audit broad or export-like access.

## Relationship To Other Architecture

- `docs/COUNTERPARTY_REGISTRY_IMPORT.md` defines source import and duplicate candidates.
- `docs/COUNTERPARTY_PURCHASES.md` defines linked purchase records.
- `docs/COUNTERPARTY_ENRICHMENT.md` defines free/public enrichment preview/apply.
- `docs/MVP_API_CONTRACTS.md` defines conceptual list/view/update/enrichment/purchase boundaries.
- `docs/MVP_STATE_MACHINES.md` defines `Counterparty` and `CounterpartyEnrichment` states.
- `docs/CUSTOMER_AUTH_AND_GUEST_ACCESS.md` and `docs/CUSTOMER_ORGANIZATION_ACCESS.md` define customer-facing ownership limits.
- `docs/CRM_DOCUMENT_CENTER.md` and `docs/CRM_TASK_MESSENGER.md` define document/chat visibility.

## Explicitly Not Implemented

This task does not add:

- search service;
- search index;
- profile UI;
- API routes;
- backend services;
- database schema;
- SQL;
- ORM;
- migrations;
- merge logic;
- enrichment runtime;
- document linking implementation;
- internal chat implementation;
- real customer/counterparty data;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- credentials, tokens, secrets, or business logic.

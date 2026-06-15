# Counterparty Enrichment And Public Company Lookup Architecture

This document defines the documentation-only architecture for free/public counterparty enrichment and company information lookup in ArtCRM.

It does not implement external API integration, HTTP clients, scraping, parsers, backend code, frontend code, API routes, database schema, SQL, ORM, migrations, UI, tests, dependencies, containers, `.env.example` changes, real customer/counterparty data, credentials, tokens, secrets, or business logic.

## Purpose

Managers need an information block in the counterparty profile that can show reviewed public/legal company data candidates:

- legal name;
- INN;
- KPP;
- OGRN/OGRNIP;
- status;
- official address;
- registration date;
- director/management candidate;
- OKVED;
- tax authority;
- source URL;
- source timestamp;
- risk/status flags.

This enrichment is reviewable candidate data until backend validation and manager action apply selected fields. Enrichment preview/request must not mutate the active counterparty registry.

## Free / Public Source Principle

The architecture should prefer free, public, and legally usable sources for MVP.

Possible candidate sources:

- official FNS open data;
- egrul.nalog.ru-style lookup;
- official registry data;
- other free/public services when legally usable;
- `Za chestny biznes` / `За честный бизнес` only as an optional candidate if free and legal access exists.

Rules:

- no paid-service dependency for MVP;
- if no free API is available, fall back to manual entry/review;
- no scraping implementation in this task;
- no credentials/API keys in docs;
- no real API calls;
- no production endpoints or tokens;
- source usage terms must be checked before implementation;
- enrichment output is candidate data until validated and applied.

## Enrichment Statuses

Use the `CounterpartyEnrichment` states from `docs/MVP_STATE_MACHINES.md`:

- `requested`;
- `previewed`;
- `validated`;
- `needs_review`;
- `applied`;
- `rejected`;
- `failed`;
- `archived`.

State boundaries:

- request/preview uses `counterparty.enrichment_request`;
- preview/request cannot mutate active counterparty fields;
- apply/reject reviewed fields uses `counterparty.enrichment_apply`;
- apply must not silently overwrite critical fields;
- failed enrichment must not block the whole counterparty profile.

## Enrichment Flow

Conceptual flow:

1. Manager requests enrichment from counterparty profile.
2. Backend creates a future enrichment request in `requested` state.
3. Future source lookup creates candidate preview data.
4. Candidate data is shown as preview, not registry truth.
5. Backend validates source, identity match, freshness, and confidence.
6. Ambiguous or conflicting data moves to `needs_review`.
7. Manager reviews field differences and source references.
8. Manager applies selected fields with `counterparty.enrichment_apply`.
9. Audit event records changed field names, source refs, reviewer, permission used, and safe summary.
10. Rejected/failed enrichment remains a quality signal and can be archived later.

No silent overwrite is allowed. Existing manually reviewed fields should not be replaced without explicit reviewer choice.

## Matching Logic

Future matching should prefer stronger identifiers before weak text matching:

- INN first;
- OGRN/OGRNIP if present;
- KPP as supporting branch/legal context where applicable;
- legal name as secondary signal;
- normalized name as weak fallback;
- address/contact signals only as supporting evidence.

Rules:

- exact INN match can produce high-confidence candidate but still requires validation before apply;
- OGRN/OGRNIP match can strengthen identity;
- legal-name-only match is not enough for silent apply;
- ambiguous result -> `needs_review`;
- no result -> `failed`, `not_found`, or `manual_review_required` future error/status;
- multiple possible matches -> manual review;
- conflicting source fields must be shown as differences, not silently resolved.

## Candidate Data Model

Conceptual enrichment preview fields:

- enrichment request ref;
- counterparty ref;
- source name;
- source URL;
- source timestamp;
- lookup key used;
- match confidence candidate;
- legal name candidate;
- INN candidate;
- KPP candidate;
- OGRN/OGRNIP candidate;
- official address candidate;
- company status candidate;
- registration date candidate;
- director/management candidate;
- OKVED candidate;
- tax authority candidate;
- risk/status flags candidate;
- field differences;
- missing fields;
- warnings;
- validation status;
- reviewer decision;
- audit refs.

Do not store secrets, credentials, raw tokens, unrestricted source payloads, or sensitive data dumps in enrichment records or audit metadata.

## Cache And Freshness

Future enrichment should track freshness because public registry data can change.

Concepts:

- source timestamp;
- last checked date;
- freshness status;
- manual refresh;
- stale data warning;
- source URL/ref;
- rate limit consideration;
- source terms/usage policy flag.

Suggested freshness statuses:

- `fresh`;
- `stale`;
- `unknown`;
- `refresh_required`;
- `source_unavailable`.

Rules:

- stale data should be visible in profile warnings;
- refresh should be manual or controlled by future policy;
- rate limits must be respected;
- cached source data should be minimized and permission-protected;
- audit should record source timestamp and refresh action without storing excessive payloads.

## Permissions

Use existing permissions:

- `counterparty.enrichment_request` for request/preview/validation flow.
- `counterparty.enrichment_apply` for applying selected reviewed fields.
- `counterparty.update` for manual profile corrections.
- `audit.view` for viewing enrichment audit history when allowed.

No new permission names are introduced by this document.

## Privacy, Legal, And Rate-Limit Boundaries

Rules:

- comply with source usage terms;
- prefer official/free/legal sources;
- store source reference and timestamp;
- avoid excessive calls;
- avoid storing secrets;
- no automatic legal conclusion;
- no automatic risk scoring that presents itself as legal advice;
- fallback to manual review when source access is unclear;
- do not expose raw source payloads to unauthorized users;
- do not pass source data to LLM agents unless a future task explicitly defines that workflow and validation.

## Profile Integration

Counterparty profile enrichment block should show:

- current registry value;
- candidate public/source value;
- source label and timestamp;
- freshness/staleness;
- difference summary;
- warnings and ambiguity flags;
- action to request enrichment;
- action to apply selected fields if reviewed;
- action to reject candidate;
- audit history link.

Only users with `counterparty.enrichment_request` can request preview. Only users with `counterparty.enrichment_apply` can apply reviewed fields.

## Error And Review Outcomes

Future safe error/status concepts:

- `not_found`;
- `multiple_matches`;
- `source_unavailable`;
- `rate_limited`;
- `ambiguous_identity`;
- `validation_failed`;
- `manual_review_required`;
- `source_terms_unknown`.

Error summaries must not include secrets, tokens, credentials, raw source payloads, or sensitive customer data. Failed enrichment should not block unrelated profile actions.

## Audit Events

Use existing taxonomy event names where applicable:

- `counterparty_enrichment.previewed`;
- `counterparty_enrichment.validated`;
- `counterparty_enrichment.needs_review`;
- `counterparty_enrichment.applied`;
- `counterparty_enrichment.rejected`;
- `counterparty_enrichment.failed`;
- `counterparty.updated` when reviewed fields are applied to the profile.

Audit metadata should include source ref, source timestamp, changed field names, reviewer ref, permission used, and safe warnings. Do not store full source payloads or secrets in audit events.

## Source Boundary: FNS, egrul, And Za Chestny Biznes

- FNS/open registry sources are preferred when free and legally usable.
- egrul.nalog.ru-style lookup is a candidate architecture boundary, not an implemented integration.
- Official registry data should be preferred over unofficial mirrors when possible.
- `За честный бизнес` may be evaluated later only if free/legal access exists and usage terms allow it.
- If a source requires paid access, credentials, scraping, or unclear terms, it is not an MVP dependency.
- Manual entry/review remains the fallback.

## Explicitly Not Implemented

This task does not add:

- external API integration;
- HTTP client;
- scraping;
- parser;
- enrichment service;
- backend implementation;
- frontend UI;
- API routes;
- database schema;
- SQL;
- ORM;
- migrations;
- source credentials;
- API keys;
- real source calls;
- real company data;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- credentials, tokens, secrets, or business logic.

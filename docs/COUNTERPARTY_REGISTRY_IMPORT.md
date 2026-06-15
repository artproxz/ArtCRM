# Counterparty Registry And amoCRM Company Import Architecture

This document defines the documentation-only architecture for the ArtCRM counterparty registry and future amoCRM company CSV import.

It does not implement backend code, frontend code, CSV parser, importer, API routes, database schema, SQL, ORM, migrations, UI, tests, dependencies, containers, `.env.example` changes, real amoCRM rows, real customer/counterparty data, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM needs a central counterparty registry as the CRM object for companies and customers. The registry should become the controlled reference point for:

- incoming requests and request cards;
- commercial offers / KP and quote versions;
- purchase records;
- CRM documents and document visibility;
- internal messages/chats linked to company context;
- supplier quote context where a customer/counterparty is relevant;
- future customer organization relation;
- analytics, data quality reports, and audit history.

Counterparty data is internal CRM data by default. It must be protected by backend permissions, field masking, audit events, and reviewable state transitions before any implementation work starts.

## Source File Assumptions

The planned import source is an amoCRM companies CSV file named `aspro_COMPANIES_only_ALL_7092(1).csv`.

Known source characteristics:

- 7,092 rows;
- 32 fields;
- company name;
- legal name;
- INN;
- responsible manager;
- source;
- customer level/tier;
- phones;
- emails;
- addresses;
- notes;
- amoCRM ID;
- linked deals;
- contact person.

INN exists only for part of the rows, approximately 3,297 rows. The CSV file and real rows must not be committed to the repository. Documentation examples must use placeholders only.

## Registry Scope

Conceptual registry objects:

- `Counterparty` - internal CRM company/customer registry record.
- `CounterpartyContact` - phone/email/person/contact channel linked to a counterparty.
- `CounterpartyAddress` - delivery, legal, or free-form address candidate.
- `CounterpartyExternalRef` - external system identity such as amoCRM company ID.
- `CounterpartyImportRow` - import preview/apply row result and validation state.
- `CounterpartySource` - normalized source/channel label.
- `CounterpartyTier` / `CounterpartyLevel` - normalized customer level or tier.
- `StaffUser` / responsible manager reference - internal responsible staff mapping.
- `Future CustomerOrganization` - future customer portal organization link, not MVP default.

These are conceptual objects only. This document does not create tables, ORM models, migrations, API routes, or services.

## External ID Strategy

Rules:

- `amoCRM ID` is the main external stable key for amoCRM imports.
- `CounterpartyExternalRef` should conceptually store source system, external ID, import batch ref, and last seen timestamp.
- Import must be idempotent: repeated import of the same amoCRM ID should update, skip, or report an existing record, not create duplicates.
- INN is important for legal matching, but it is not always present.
- INN can be missing, duplicated, mistyped, or shared by branch/source data in ways that require review.
- INN must not be the only unique identifier.
- Legal name and normalized display name are secondary matching signals.
- Missing INN means no automatic merge by name alone.

Suggested idempotency decision order:

1. Same source system and same amoCRM ID -> same imported source record.
2. Same INN and compatible legal/name signals -> duplicate candidate or safe update candidate depending on future policy.
3. Same normalized legal name -> duplicate candidate, never silent merge.
4. Same normalized phone/email/address cluster -> duplicate candidate.
5. Name-only match without INN -> manual review candidate.

## Field Mapping

| Source field | Target entity | Target field | Required/optional | Normalization | Notes |
| --- | --- | --- | --- | --- | --- |
| amoCRM ID | CounterpartyExternalRef | `external_id` | Required for amoCRM import | Trim, preserve as string | Main stable key for idempotent import. |
| source system | CounterpartyExternalRef | `source_system` | Required | Constant such as `amocrm` | Placeholder only; no integration now. |
| company name | Counterparty | `display_name` | Required if legal name missing | Trim, collapse whitespace, normalize quotes/case for matching | Must preserve original source value separately in import row. |
| legal name | Counterparty | `legal_name` | Optional | Normalize legal forms and whitespace | Secondary legal matching signal. |
| INN | Counterparty | `inn` | Optional | Digits only, validate expected length later | Important but not unique enough alone. |
| KPP | Counterparty | `kpp` | Future optional | Digits only | Future field if source/provider has it. |
| OGRN/OGRNIP | Counterparty | `ogrn` / `ogrnip` | Future optional | Digits only | Future enrichment/import field. |
| responsible manager | StaffUser/responsible manager reference | `responsible_manager_ref` | Optional | Map by normalized staff name/email if available | Unknown manager must be reported in preview. |
| source | CounterpartySource | `source_code` / `source_label` | Optional | Map to controlled labels | Unknown source should be reviewable. |
| customer level/tier | CounterpartyTier/Level | `tier_code` / `tier_label` | Optional | Map to controlled labels | Unknown level should not block all rows. |
| phones | CounterpartyContact | `phone` | Optional | Normalize punctuation, country prefix, extensions | Invalid phone goes to warning/review. |
| emails | CounterpartyContact | `email` | Optional | Lowercase domain/local policy, trim | Invalid email goes to warning/review. |
| addresses | CounterpartyAddress | `address_text` | Optional | Trim, collapse whitespace, parse city/region when safe | Do not over-parse without validation. |
| notes | CounterpartyImportRow / Counterparty | `source_notes` / safe note refs | Optional | Preserve text with safe redaction policy | Notes may contain sensitive data; avoid dumping into audit. |
| linked deals | CounterpartyImportRow | `linked_deal_refs_candidate` | Optional | Preserve source refs as candidates | Do not create deals in this task. |
| contact person | CounterpartyContact | `contact_person_name` | Optional | Trim, split only when safe | May create contact candidate later. |
| row number | CounterpartyImportRow | `source_row_number` | Required for preview | Numeric import context | Helps review errors without storing raw rows in docs. |
| raw row checksum | CounterpartyImportRow | `source_row_hash` | Future optional | Hash source row | Helps idempotency/audit without exposing raw data. |
| customer organization candidate | Future CustomerOrganization | `organization_candidate_ref` | Future optional | Backend-reviewed link only | Customer org sharing is future, not MVP default. |

## Normalization

Normalization is a future backend responsibility. This document records desired behavior only.

- Company name normalization: trim, collapse whitespace, normalize quotes, remove repeated punctuation, create lowercase matching key while preserving original display text.
- Legal name normalization: trim, normalize common legal-form spelling, preserve original source legal name, produce a matching key.
- INN cleanup: keep digits only, validate expected length later, report empty or invalid INN as data quality flag.
- KPP/OGRN future fields: digits-only cleanup and validation are future enrichment/import rules.
- Phone normalization: split multi-value cells when safe, trim, remove visual separators, preserve extension notes, mark invalid numbers.
- Email normalization: trim, lowercase domains, validate shape, split multi-value cells when safe, mark invalid emails.
- Address cleanup: trim, collapse whitespace, detect city/region candidates when safe, keep original address text.
- Responsible manager mapping: map source staff label to `StaffUser` reference; unknown manager remains a preview warning.
- Source mapping: map source labels to controlled `CounterpartySource`; unknown source is reviewable but should not silently invent a source.
- Customer level/tier mapping: map source tier labels to controlled `CounterpartyTier`; unknown tier goes to preview warning.
- Notes preservation: preserve source notes as internal data with safe redaction rules; do not copy notes into audit metadata wholesale.
- Contact person extraction: treat as contact candidate; do not invent role, email, or phone relationships.

## Duplicate Detection

Duplicate detection must create reviewable candidates, not silent merges.

| Signal | Meaning | Default action |
| --- | --- | --- |
| Same amoCRM ID | Same imported source company record. | Idempotent update/skip candidate. |
| Same INN | Possible same legal counterparty. | Duplicate candidate; manual review if conflicting fields. |
| Duplicate INN with different legal names | Possible branch/source conflict or bad data. | `needs_review`, no silent merge. |
| Same normalized legal name | Possible duplicate. | Duplicate candidate, manual review. |
| Same normalized phone/email | Possible related company/contact duplicate. | Duplicate candidate. |
| Same company name plus same city/address | Possible duplicate. | Duplicate candidate. |
| Missing INN with similar name | Weak match. | Never auto-merge by name only. |
| Same phone/email across unrelated-looking names | Possible shared contact or bad source data. | Warning and manual review. |

Merge review must preserve source refs, aliases, original source values, and audit history. Future merge decisions use `counterparty.merge_review` and must emit `counterparty.merge_candidate_reviewed`.

## Import Flow

The import flow aligns with the `CounterpartyImport` state machine from `docs/MVP_STATE_MACHINES.md`:

- `uploaded`;
- `previewed`;
- `validated`;
- `needs_review`;
- `applied`;
- `partially_applied`;
- `failed`;
- `canceled`;
- `archived`.

Conceptual flow:

1. Manager/admin selects a controlled file source for future import.
2. Backend creates an import record in `uploaded` state.
3. Import preview parses rows conceptually and creates a preview report without registry mutation.
4. Validation checks required fields, amoCRM ID idempotency, INN quality, contacts, addresses, source/tier mapping, and responsible manager mapping.
5. Duplicate candidates are grouped for manager review.
6. Rows ready to apply are separated from rows requiring review.
7. Manager reviews duplicates and problem rows.
8. Apply uses `counterparty.import_apply` and creates/updates only validated records.
9. Partial apply is allowed if safe rows can be applied while problem rows remain failed/reviewable.
10. Error report records failed rows with safe summaries.
11. Audit events record preview, validation, apply, partial apply, failure, and merge review decisions.
12. Import can be canceled or archived without deleting audit history.

Import preview/request must not mutate active counterparty fields. Registry mutation is allowed only through reviewed import apply or counterparty update workflows.

## Import Preview Report

The preview report should include safe aggregate and row-level review metadata:

- total rows;
- valid rows;
- rows with missing INN;
- rows with invalid INN shape;
- rows with duplicate INN;
- duplicate candidates by amoCRM ID, INN, legal name, contact, and address cluster;
- invalid phones;
- invalid emails;
- unknown responsible managers;
- unknown customer level/source;
- rows requiring manual review;
- rows ready to apply;
- skipped rows;
- failed rows;
- safe error examples;
- import batch ref;
- source file metadata placeholder, not real file content;
- idempotency summary;
- merge review queue summary.

Example values must remain placeholders. Do not include real row content, company names, phones, emails, or addresses in documentation.

## Audit Events

Use existing audit taxonomy event names:

- `counterparty_import.previewed`;
- `counterparty_import.validated`;
- `counterparty_import.needs_review`;
- `counterparty_import.applied`;
- `counterparty_import.partially_applied`;
- `counterparty_import.failed`;
- `counterparty.created`;
- `counterparty.updated`;
- `counterparty.merge_candidate_reviewed`.

Audit metadata should include safe references, counts, validation status, permission used, import batch ref, source system, and reviewer refs. Audit metadata must not contain raw CSV rows, secrets, credentials, tokens, full notes, or unrestricted customer data.

## Permissions

Use existing permission names only:

- `counterparty.import_preview` for preview and validation report generation.
- `counterparty.import_apply` for applying validated rows.
- `counterparty.update` for reviewed profile field corrections.
- `counterparty.merge_review` for duplicate/merge decisions.
- `counterparty.search` for viewing registry/search context.
- `counterparty.export` for any future export of counterparty data.
- `audit.view` for viewing audit history when allowed.

No new permission names are introduced by this document.

## Relationship To Other Architecture

- `docs/MVP_API_CONTRACTS.md` defines the Counterparty / Customer Registry API boundary conceptually.
- `docs/MVP_STATE_MACHINES.md` defines `CounterpartyImport` and `Counterparty` transition guards.
- `docs/PERMISSION_MATRIX.md` is the permission source of truth.
- `docs/AUDIT_EVENT_TAXONOMY.md` defines event names and safe audit metadata rules.
- `docs/CUSTOMER_ORGANIZATION_ACCESS.md` remains future architecture; import does not automatically create organization sharing.
- `docs/CRM_ANALYTICS_DASHBOARDS.md` may later consume import quality and data freshness metrics.

## Explicitly Not Implemented

This task does not add:

- CSV parser;
- importer;
- upload/download implementation;
- backend services;
- API routes;
- database schema;
- SQL;
- ORM;
- migrations;
- frontend UI;
- external amoCRM integration;
- real CSV rows;
- real customer/counterparty data;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- credentials, tokens, secrets, or business logic.

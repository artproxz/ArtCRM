# ArtCRM Domain Model

This document defines the initial domain model for ArtCRM. It is intentionally conceptual and does not define SQL tables, ORM classes, migrations, database constraints, or storage implementation.

## Validation Boundary

All entities below are owned by backend domain validation. AI output, mail extraction data, catalog suggestions, and integration payloads are candidate data until the backend validates them.

Unvalidated data must not be written into business tables as authoritative CRM, catalog, document, or 1C exchange data.

## RequestCard

### Purpose

Represents an incoming customer request created from mail intake and operator review. It is the central object connecting source mail, extracted positions, counterparty context, CRM workflow, and later document generation.

### Key Fields

- `id` - stable identifier.
- `source_mail_id` - reference to the source mail record or intake item.
- `counterparty_id` - linked Counterparty when known and validated.
- `subject` - request subject or normalized title.
- `status` - draft, needs_review, validated, converted, canceled, or later workflow states.
- `received_at` - source mail receive timestamp.
- `created_by_agent_run_id` - AgentRun that proposed the initial draft.
- `validation_status` - backend validation state.
- `review_notes` - operator notes and unresolved issues.

### Relationships

- Has many RequestPosition records.
- May link to one Counterparty.
- May create or update one Deal.
- May link to one Project after CRM qualification.
- References AgentRun for traceability.

### Data Requiring Backend Validation

- Counterparty identity and contact details.
- Request subject and inferred intent.
- Source mail references.
- Status transitions.
- Any AI-extracted summary, priority, deadline, or commercial condition.

## RequestPosition

### Purpose

Represents one requested item, material, service, or line extracted from a RequestCard. It is matched against the structured catalog before it can be used for CRM, documents, or 1C exchange.

### Key Fields

- `id` - stable identifier.
- `request_card_id` - parent RequestCard.
- `raw_text` - original or normalized source text from mail extraction.
- `item_name` - candidate item name.
- `quantity` - requested quantity when known.
- `unit` - unit of measure when known.
- `attributes` - candidate structured attributes.
- `catalog_item_id` - approved CatalogItem match, if selected.
- `match_status` - unmatched, candidates_found, approved, rejected, or needs_review.
- `validation_status` - backend validation state.

### Relationships

- Belongs to one RequestCard.
- May link to one approved CatalogItem.
- May be proposed by one or more AgentRun records.
- May contribute to Deal and document line items after validation.

### Data Requiring Backend Validation

- Quantity, unit, dimensions, article numbers, and attributes.
- Catalog match candidate and final selected CatalogItem.
- AI-generated item names, substitutions, and normalization.
- Any values intended for documents, CRM, or 1C.

## CatalogItem

### Purpose

Represents an item in the structured catalog used for matching request positions and generating validated commercial or integration data.

### Key Fields

- `id` - stable identifier.
- `sku` - internal or external catalog code when available.
- `name` - validated catalog name.
- `category` - catalog grouping.
- `attributes` - structured catalog attributes.
- `unit` - default unit of measure.
- `is_active` - availability for matching and business use.
- `source_system` - source of catalog authority, if applicable.

### Relationships

- May be linked from many RequestPosition records.
- May be referenced by Deal, Project, document, and 1C exchange workflows.

### Data Requiring Backend Validation

- Catalog imports and updates.
- AI-proposed substitutions or aliases.
- Any catalog field used for price, stock, document, or 1C exchange decisions.

## Counterparty

### Purpose

Represents a customer, supplier, or organization participating in a request, deal, project, or document workflow.

### Key Fields

- `id` - stable identifier.
- `name` - validated legal or display name.
- `tax_id` - tax or registration identifier when applicable.
- `contacts` - validated contact references.
- `email_domains` - validated domains associated with the counterparty.
- `status` - active, needs_review, duplicate_candidate, archived.
- `source_refs` - references to mail, CRM, or integration sources.

### Relationships

- May own many RequestCard records.
- May own many Deal records.
- May be associated with many Project records.
- May be synchronized with 1C after validation.

### Data Requiring Backend Validation

- Legal names, tax identifiers, contacts, and email domains.
- Duplicate detection and merge decisions.
- AI-inferred counterparty identity.
- Any data sent to CRM, documents, or 1C.

## Deal

### Purpose

Represents a commercial opportunity created from a validated RequestCard and connected to CRM workflow.

### Key Fields

- `id` - stable identifier.
- `counterparty_id` - linked Counterparty.
- `request_card_id` - source RequestCard.
- `project_id` - related Project when applicable.
- `status` - qualification, offer_preparation, negotiation, won, lost, canceled, or later workflow states.
- `owner_id` - responsible user or team reference.
- `amount_estimate` - validated commercial estimate when available.
- `next_action_at` - planned follow-up date.

### Relationships

- Belongs to one Counterparty.
- May originate from one RequestCard.
- May belong to one Project.
- May produce documents and 1C exchange payloads.

### Data Requiring Backend Validation

- Amounts, deadlines, statuses, ownership, and commercial terms.
- AI-generated qualification notes or next actions.
- Any value used in documents or 1C exchange.

## Project

### Purpose

Represents a larger business context that can group deals, requests, documents, and implementation activity.

### Key Fields

- `id` - stable identifier.
- `name` - validated project name.
- `counterparty_id` - primary Counterparty.
- `status` - planning, active, paused, completed, canceled, or later workflow states.
- `description` - validated project summary.
- `owner_id` - responsible user or team reference.

### Relationships

- May contain many Deal records.
- May link to many RequestCard records indirectly through deals.
- May be associated with documents and 1C exchange workflows.

### Data Requiring Backend Validation

- Project name, ownership, status, dates, and descriptions.
- AI-generated summaries, risk notes, and planning suggestions.
- Any project data exported to documents or external systems.

## AgentRun

### Purpose

Represents one execution of an AI-assisted backend workflow, such as Mail Reader Agent extraction or catalog matching assistance. AgentRun provides traceability, auditability, and validation status for AI outputs.

### Key Fields

- `id` - stable identifier.
- `agent_type` - mail_reader, catalog_matcher, summarizer, or future backend agent type.
- `input_ref` - reference to the controlled backend input.
- `output_ref` - reference to stored candidate output when retained.
- `status` - queued, running, succeeded, failed, rejected, or validated.
- `validation_result` - backend validation outcome.
- `started_at` - start timestamp.
- `finished_at` - finish timestamp.
- `error_summary` - non-secret error summary when applicable.

### Relationships

- May create or update RequestCard candidate data.
- May propose RequestPosition values.
- May propose CatalogItem match candidates.
- May be linked to operator review decisions.

### Data Requiring Backend Validation

- Entire AI output payload.
- Extracted fields, summaries, classifications, and match suggestions.
- Error details before logging or UI display.
- Any data that could affect CRM, documents, catalog, 1C, or business tables.

## Deferred Modeling Decisions

The following decisions are intentionally deferred:

- Physical database schema.
- ORM model names and relationships.
- Migration strategy.
- Event schema and queue implementation.
- API request and response contracts.
- Authorization model and permission matrix.

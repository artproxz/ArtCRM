# ArtCRM API Contracts

This document defines conceptual API contracts for the first ArtCRM backend boundary. It describes API groups, responsibilities, inputs, outputs, errors, callers, and validation rules only. It does not define FastAPI routes, OpenAPI schemas, DTO classes, SQL, ORM models, migrations, containers, or runtime dependencies.

All APIs are backend-owned. The frontend and integrations must treat backend responses as the only trusted interface for RequestCard, RequestPosition, AgentRun, and catalog matching workflows.

## Common Principles

- Backend is the only component allowed to access mail, Ollama, 1C, databases, queues, cache, and secrets.
- Frontend calls backend APIs only and never calls Ollama, mail, 1C, databases, or catalog storage directly.
- AI output, mail extraction output, and catalog match suggestions are candidate data until backend validation and operator approval.
- APIs must expose validation status, unresolved fields, and review warnings instead of silently accepting ambiguous data.
- API responses must not expose secrets, mail credentials, raw tokens, private keys, model paths, or internal integration credentials.
- Business tables must receive only backend-validated and approved data.

## RequestCard API

### Purpose

RequestCard API manages incoming request cards created from mail intake, Mail Reader Agent output, and operator review. It is the main workflow surface for turning incoming mail into validated CRM-ready request data.

### Main Operations

- List request cards with filters by status, counterparty, received date, validation state, and review state.
- Get request card details with positions, source references, validation warnings, and agent trace links.
- Create a draft request card from validated mail intake or controlled backend input.
- Update editable draft fields through backend validation.
- Mark a request card as needing review.
- Approve a request card after required fields and positions are valid.
- Reject a request card with a reason.
- Archive a request card that should no longer participate in active workflow.

### Input Data

- Source mail reference or backend intake identifier.
- Candidate counterparty reference or counterparty candidate fields.
- Subject or normalized title.
- Operator edits and review notes.
- Requested status transition.
- Validation decision and rejection reason when applicable.

### Output Data

- RequestCard identifier and current lifecycle status.
- Linked RequestPosition summaries.
- Counterparty candidate or approved Counterparty reference.
- Validation status and unresolved fields.
- Source mail reference metadata safe for UI display.
- Related AgentRun references.
- Audit-friendly timestamps and actor references.

### Main Errors

- RequestCard not found.
- Invalid status transition.
- Missing required fields.
- Counterparty candidate requires review.
- Request positions are not ready for approval.
- Source mail reference is invalid or inaccessible.
- Permission denied for caller role.
- Conflict caused by concurrent update.

### Allowed Callers

- Frontend operator UI through authenticated backend API.
- Backend Mail Reader Agent workflow after backend validation.
- Backend CRM workflow services.
- Backend administrative or audit tools.

External systems must not create or mutate RequestCards directly without passing through backend-controlled integration logic.

### Candidate Data Requiring Backend Validation

- AI-extracted request summaries, subject, priority, due dates, and commercial notes.
- Counterparty identity inferred from email sender or message body.
- Source mail references and extracted contact data.
- Any status transition requested by frontend or agent workflow.
- Any value later used by CRM, documents, catalog matching, or 1C exchange.

## RequestPosition API

### Purpose

RequestPosition API manages line items extracted from a RequestCard. It keeps raw request text, normalized candidate fields, validation state, and approved catalog match references separate until backend validation is complete.

### Main Operations

- List positions for a RequestCard.
- Get position details with validation warnings and match status.
- Create draft positions from validated Mail Reader Agent extraction.
- Update draft fields such as item name, quantity, unit, and attributes.
- Mark positions as ready for catalog matching.
- Approve a catalog match for a position.
- Reject a position or match candidate with a reason.
- Archive positions that should no longer be used.

### Input Data

- Parent RequestCard identifier.
- Raw extracted text or controlled operator-entered text.
- Candidate item name, quantity, unit, and attributes.
- Requested match status transition.
- Selected CatalogItem candidate when approving a match.
- Operator review notes or rejection reason.

### Output Data

- RequestPosition identifier and lifecycle status.
- Parent RequestCard reference.
- Raw text and normalized candidate fields safe for display.
- Quantity, unit, and attributes with validation status.
- Catalog match status and approved CatalogItem reference when available.
- Match candidate summaries returned by Catalog Matching API.
- Warnings for missing, contradictory, or low-confidence data.

### Main Errors

- RequestPosition not found.
- Parent RequestCard not found or not editable.
- Invalid quantity, unit, or attribute format.
- Position is not ready for matching.
- Catalog match candidate is invalid or expired.
- Invalid status transition.
- Permission denied for caller role.
- Conflict caused by concurrent update.

### Allowed Callers

- Frontend operator UI through authenticated backend API.
- Backend Mail Reader Agent workflow for candidate creation.
- Backend Catalog Matching workflow.
- Backend CRM and document workflow services after validation.

### Candidate Data Requiring Backend Validation

- AI-extracted line item text, item names, quantities, units, article numbers, and attributes.
- Operator edits that affect catalog matching, documents, CRM, or 1C exchange.
- Catalog match references before approval.
- Any normalized value derived from raw mail text.

## AgentRun API

### Purpose

AgentRun API provides traceability and controlled interaction for AI-assisted backend workflows such as Mail Reader Agent, Product Selector / CRM Position Intent Agent, Manager Catalog Assistant, Client Catalog Assistant, and Response Draft Agent. It exposes run status, validation outcome, and non-secret execution summaries.

AgentRun API does not give the frontend direct access to Ollama or any AI runtime. Frontend may request or observe backend-managed workflows only through authenticated backend APIs.

Full AgentRun schema, validation error taxonomy, prompt/model versioning policy, retry/fallback rules, and quality loop are defined in [AgentRun Schema and Quality Policy](AGENT_RUN.md).

### Main Operations

- List agent runs by type, status, RequestCard, RequestPosition, prompt version, model name, and time range.
- Get agent run details with input references, output references, validation result, and safe error summary.
- Start a backend-controlled Mail Reader Agent run for an eligible mail intake item.
- Start a backend-controlled catalog assistance run for eligible positions.
- Start a backend-controlled Response Draft Agent run for customer-response text only.
- Mark agent output as validated, rejected, or requiring operator review.
- Record manager quality feedback, correction references, and review decisions.
- Archive old agent run records according to retention policy.

### Input Data

- Agent type such as mail_reader, position_intent, manager_catalog_assistant, client_catalog_assistant, or response_draft.
- Agent metadata such as `agent_name`, `agent_version`, `prompt_version`, `model_name`, and `model_provider` / `runtime`.
- Controlled backend input reference, not raw unbounded frontend text.
- RequestCard or RequestPosition references when applicable.
- Operator or backend workflow trigger context.
- Validation decision after backend checks.
- Quality review decision, correction reference, or safe review comment.

### Output Data

- AgentRun identifier, agent name, agent type, status, retry count, and timestamps.
- Input reference and output reference safe for audit.
- `agent_version`, `prompt_version`, `model_name`, `model_provider` / `runtime`, and `input_hash` metadata.
- `raw_response_reference` retained according to policy and redaction rules.
- `normalized_response` with backend-normalized candidate data.
- `validation_status` and `validation_errors` for schema, safety, business, or consistency checks.
- `confidence` marker.
- Review metadata such as reviewed_by, review_decision, and safe review_comment.
- Candidate data summary safe for UI display.
- Non-secret error summary when the run fails.

### Main Errors

- Agent type is not supported.
- Input reference is missing, invalid, or not eligible.
- Backend AI runtime is unavailable.
- Agent output schema is invalid.
- Validation failed.
- Permission denied for caller role.
- Run is already completed, rejected, approved, or archived.
- Retry limit exceeded.

### Validation Error Taxonomy

AgentRun validation errors use the taxonomy defined in [AgentRun Schema and Quality Policy](AGENT_RUN.md):

- invalid_json
- missing_required_field
- unexpected_field
- invalid_enum
- invalid_quantity
- invalid_unit
- low_confidence
- ambiguous_position
- critical_mismatch
- unsafe_content
- timeout
- ollama_unavailable
- validation_exception

### Retry and Fallback Contract

- API may allow one controlled retry for invalid_json or temporary runtime failures.
- Retry must not be indefinite.
- After repeated failure, affected candidate data moves to needs_review.
- Agent failures must not block the entire RequestCard by default.
- Error summaries must be redacted and safe for UI display.

### Allowed Callers

- Backend workflow services.
- Frontend operator UI for status reads and review decisions through backend API.
- Backend administrative, audit, or quality-review tools.

Frontend must not call Ollama or any AI runtime directly. External systems must not start AgentRun records directly.

### Candidate Data Requiring Backend Validation

- Entire AI output payload.
- Extracted RequestCard fields.
- Extracted RequestPosition fields.
- Catalog explanation and ranking suggestions.
- Response draft text before sending.
- Classifications, summaries, confidence scores, and explanations.
- Error text before exposing it to UI or logs.

## Catalog Matching API

### Purpose

Catalog Matching API provides backend-owned matching between validated RequestPosition drafts and structured catalog data. It separates match suggestions from approved catalog links.

Backend Catalog Matcher is a backend service, not a pure LLM agent. LLM assistance may explain or rank candidates, but backend matching rules own final score handling, critical mismatch detection, analog flags, `needs_review`, and approval boundaries.

### Main Operations

- Request match candidates for one RequestPosition.
- Request batch match candidates for positions in one RequestCard.
- Get match candidates and explanations for a position.
- Approve a candidate CatalogItem for a position.
- Reject a candidate with a reason.
- Mark a position as unresolved when no candidate is acceptable.

### Input Data

- RequestPosition identifier.
- Validated candidate item name, quantity, unit, and attributes.
- Optional operator-provided search hints.
- Selected CatalogItem candidate for approval.
- Rejection or unresolved reason.

### Output Data

- Match candidate identifiers.
- CatalogItem references safe for UI display.
- Confidence level or ranking.
- Critical mismatch flag.
- Analog flag.
- `needs_review` decision.
- Explanation and unresolved fields.
- Warnings for ambiguous or incomplete data.
- Final approved match reference when selected.

### Main Errors

- RequestPosition not found.
- Position is not ready for matching.
- Catalog data is unavailable.
- Candidate is invalid, inactive, or no longer applicable.
- Match approval violates backend validation rules.
- Permission denied for caller role.
- Conflict caused by concurrent update.

### Allowed Callers

- Frontend operator UI through authenticated backend API.
- Backend RequestPosition workflow.
- Backend catalog matching services.

No caller may bypass backend validation and write catalog links directly into business records.

### Candidate Data Requiring Backend Validation

- Match candidates and confidence scores.
- AI-assisted substitutions, aliases, and explanations.
- Operator-selected candidate before final approval.
- Any catalog reference used by documents, CRM, pricing, stock, or 1C exchange.

## Future Document and Invoice Generation API

### Purpose

Future document/invoice generation API will generate invoices, commercial proposals, PDFs, letters, print forms, and accompanying documents through backend-only deterministic templates or scripts.

This API is intentionally documented as a future backend boundary only. It is not implemented in this task.

### Input Data

- Approved RequestCard reference.
- Approved RequestPosition references.
- Approved CatalogItem matches.
- Validated Counterparty and requisites.
- Backend-calculated price, VAT, totals, amount in words, and delivery terms.
- Selected backend document template.

### Output Data

- Generated document reference.
- Render status.
- Non-secret validation warnings.
- Safe preview metadata.

### Main Errors

- RequestCard is not approved.
- One or more positions are not approved.
- Catalog match is unresolved or rejected.
- Counterparty requisites are missing or invalid.
- Financial values are missing backend validation.
- Template is unavailable or invalid.

### Allowed Callers

- Backend document workflow services.
- Frontend manager UI through authenticated backend API.
- Backend administrative or audit tools.

### Non-Negotiable Validation Rules

- API must accept only validated/approved data.
- API must not trust LLM-generated financial values.
- LLM must not calculate sums, VAT, prices, requisites, totals, amount in words, delivery terms, signatures, seals, or final document values.
- Response Draft Agent may provide only text for messages, cover letters, explanations, and clarification questions.
- Final invoice, commercial proposal, and PDF generation must be deterministic and backend-owned.

## Deferred Contract Decisions

The following decisions are intentionally deferred to future implementation tasks:

- Concrete HTTP paths and methods.
- Request and response schema formats.
- Authentication and authorization model.
- Pagination, sorting, and filtering conventions.
- Error code taxonomy beyond documented AgentRun taxonomy.
- Idempotency and retry rules beyond documented AgentRun retry/fallback policy.
- API versioning policy.
- OpenAPI generation.

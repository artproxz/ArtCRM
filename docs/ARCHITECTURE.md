# ArtCRM Architecture

This document records the architecture foundation for ArtCRM before infrastructure and backend implementation begins. It defines responsibilities, integration boundaries, and validation principles only. It does not introduce runtime code, framework skeletons, containers, SQL, ORM models, or dependencies.

## Product Flow

ArtCRM is built around the incoming request processing flow:

1. Mail inbox receives a customer message.
2. Mail Reader Agent analyzes the message through backend-controlled AI execution.
3. Backend creates or updates a RequestCard draft.
4. Backend extracts RequestPosition drafts from the request content.
5. Backend normalizes positions against the structured catalog.
6. Backend Catalog Matcher proposes CatalogItem matches.
7. Validated data moves into CRM entities such as Deal, Project, and Counterparty.
8. Documents are generated from validated CRM data.
9. Approved data is exchanged with 1C through backend-only integration.

## Main Modules

### Frontend

The frontend is the user interface for operators and managers. It displays request cards, positions, catalog match suggestions, CRM state, validation warnings, and document workflow status.

The frontend must not access Ollama, mail servers, 1C, databases, secrets, or model configuration directly. All reads and writes go through backend APIs.

### Backend

The backend is the only trusted application boundary. It owns validation, authorization, domain rules, persistence boundaries, AI orchestration, integration with external systems, and audit trails.

The backend is the only component allowed to communicate with:

- Ollama or any local AI runtime.
- Mail servers and mail credentials.
- 1C integration endpoints.
- Database and cache services.
- Secrets and integration configuration.
- Catalog matching logic and normalized catalog access.

### Mail Reader Agent

Mail Reader Agent is an AI-assisted backend workflow. It reads mail content supplied by backend mail integration, extracts structured draft data, and returns candidate fields for backend validation.

Agent output is never saved directly into business tables. Backend validates, normalizes, and approves every extracted value before it becomes business data.

### Backend Catalog Matcher

Backend Catalog Matcher compares request positions against the structured catalog and returns match candidates with confidence, reasons, and unresolved fields. It is backend-owned because catalog matching requires domain rules, validation, auditability, and access to internal catalog data.

### CRM Module

The CRM module manages Counterparty, Deal, Project, RequestCard state, and document workflow state. It consumes only validated request and catalog data.

### Documents Module

The documents module prepares commercial offers, internal documents, and exchange-ready artifacts from validated CRM data. Document generation must not use unvalidated AI output as authoritative data.

### Integration Layer

The integration layer is backend-only. It contains adapters for mail, 1C, AI runtime access, catalog matching, persistence, cache, and future external services.

## Frontend and Backend Responsibility Boundary

Frontend responsibilities:

- Present request cards, positions, catalog suggestions, CRM state, and validation status.
- Collect user decisions, corrections, approvals, and rejection reasons.
- Send user actions to backend APIs.
- Avoid storing secrets or connecting directly to infrastructure services.

Backend responsibilities:

- Own all domain validation and state transitions.
- Execute Mail Reader Agent and Catalog Matcher workflows.
- Validate all AI-generated outputs before persistence.
- Own access to mail, 1C, Ollama, databases, cache, and secrets.
- Produce audit events for agent runs, user approvals, integration calls, and data changes.
- Protect business tables from unvalidated or ambiguous data.

## Incoming Mail Processing Flow

1. Backend mail integration receives or fetches an incoming email.
2. Backend stores raw mail metadata and content in a controlled intake area.
3. Backend starts a Mail Reader Agent run with explicit input and trace metadata.
4. Mail Reader Agent extracts draft counterparty, request, and position information.
5. Backend validates required fields, data types, source references, and confidence markers.
6. Backend creates or updates a RequestCard draft.
7. Backend creates RequestPosition drafts linked to the RequestCard.
8. Operator reviews unresolved fields and low-confidence extraction results.
9. Approved data becomes available for catalog matching and CRM workflow.

## Mail Reader Agent Flow

1. Backend selects an eligible incoming email.
2. Backend prepares the agent prompt and context from approved inputs only.
3. Backend calls the local AI runtime through a backend-only adapter.
4. Agent returns structured candidate data and extraction notes.
5. Backend validates the response schema and rejects malformed output.
6. Backend checks field-level confidence, required fields, and source references.
7. Backend stores the AgentRun record with inputs, outputs, status, and validation result.
8. Backend exposes only validated draft data and warnings to the frontend.

## Request Card Creation Flow

1. Backend receives validated mail extraction candidates.
2. Backend identifies or creates a Counterparty candidate.
3. Backend creates a RequestCard draft with source mail references.
4. Backend attaches RequestPosition drafts to the RequestCard.
5. Backend marks incomplete fields for operator review.
6. Operator confirms, edits, or rejects candidate values through the frontend.
7. Backend applies approved changes and records audit metadata.

## Request Position Processing Flow

1. Backend receives position candidates from Mail Reader Agent output.
2. Backend validates quantity, unit, free-text item name, requested attributes, and source references.
3. Backend rejects or flags incomplete and contradictory values.
4. Backend creates RequestPosition drafts linked to the RequestCard.
5. Backend sends validated draft positions to Backend Catalog Matcher.
6. Operator reviews suggested catalog matches and unresolved positions.
7. Backend stores only approved catalog links and normalized values.

## Catalog Matching Flow

1. Backend receives a validated RequestPosition draft.
2. Backend Catalog Matcher searches structured catalog data.
3. Matcher returns candidate CatalogItem links with confidence and explanation.
4. Backend validates that candidates match allowed catalog structure and business constraints.
5. Frontend displays candidates and unresolved fields to the operator.
6. Operator selects, edits, or rejects the match.
7. Backend persists the approved catalog relationship and audit trail.

## 1C Integration

1C integration is backend-only. The frontend must never call 1C directly and must never store 1C credentials.

Backend responsibilities for 1C integration:

- Prepare exchange payloads only from validated CRM and document data.
- Validate required fields before sending to 1C.
- Track outbound and inbound integration status.
- Record errors without exposing secrets in logs or UI.
- Keep retries and reconciliation explicit and auditable.

## Mail Integration

Mail integration is backend-only. Mail credentials, server settings, tokens, and mailbox state are never exposed to frontend code.

Backend responsibilities for mail integration:

- Fetch or receive mail through configured backend adapters.
- Store source references needed for audit and traceability.
- Avoid saving secrets in request data, logs, or UI payloads.
- Pass only controlled content into Mail Reader Agent workflows.

## AI Safety and Validation Principles

- AI output is always treated as untrusted candidate data.
- Backend validates AI response schema before using any field.
- Backend validates required fields, types, references, confidence, and business constraints.
- Backend stores AgentRun metadata for traceability.
- Backend never writes unvalidated AI output into business tables.
- Operator approval is required for ambiguous, low-confidence, or business-critical values.
- Logs must not contain secrets, credentials, tokens, full mail access data, or model paths.
- Future persistence and integration tasks must preserve the backend-only security boundary.

## Deferred Implementation

The following work is intentionally deferred to later tasks:

- FastAPI application skeleton.
- React application skeleton.
- PostgreSQL schema and migrations.
- Redis cache or queue setup.
- Podman or Docker Compose configuration.
- Mail, 1C, Ollama, and database adapters.
- Business logic and domain service implementation.

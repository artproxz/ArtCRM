# ArtCRM Agent Platform Foundation

This document fixes the ArtCRM agent platform boundaries before backend, FastAPI, Podman, PostgreSQL, and Redis implementation begins. It separates LLM agents from backend-only services and records that agents produce candidate data, while backend services and managers make final business decisions.

Agent and backend-service JSON/DTO contracts are defined in [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md). AgentRun audit and quality policy is defined in [AgentRun Schema and Quality Policy](AGENT_RUN.md). Product Selector quality evaluation is defined in [Product Selector Agent Quality Evaluation Plan](PRODUCT_SELECTOR_EVAL.md). Tender Reader mode and tender filtering rules are defined in [Tender Reader Rules](TENDER_READER_RULES.md).

## Core Rule

LLM agents help extract, structure, explain, and draft text. They do not own final business truth.

Backend services own validation, deterministic calculations, persistence boundaries, catalog matching decisions, document generation, integration calls, and audit trails. A manager may approve or reject candidate data through the frontend, but the backend enforces the rules.

Tender Reader output is also candidate data only. Backend rules and manager review decide final tender keep/skip/escalate policy.

## Readiness Status

Existing / available but documented as contracts:

- Mail Reader Agent generally exists as model/logic, but its JSON contract must be formally fixed and validated by backend.
- CRM Position Intent Agent / Product Selector Agent generally exists as model/logic, but the current result is not accepted by the product owner. It requires separate future quality testing and possible rework.

Target / not implemented yet:

- Tender Reader mode for Mail Reader Agent.
- Future Tender Monitor Agent boundary.
- Client Catalog Assistant.
- Manager Catalog Assistant.
- Response Draft Agent.
- Backend Catalog Matcher.
- Invoice/PDF Generator.
- Agent Orchestrator.
- Agent Validation Service.
- Document Template Service.

This document describes boundaries and target contracts. It must not be read as proof that all listed agents or backend-only services are already implemented.

## LLM Agent Map

### Mail Reader Agent

Readiness: existing / available as model/logic; JSON contract formalized in `AGENT_JSON_SCHEMAS.md`.

Purpose:

- Process dirty incoming mail content.
- Extract candidate RequestCard and RequestPosition fields.
- Identify missing or ambiguous information.
- Produce structured candidate data for backend validation.

Allowed outputs:

- Candidate counterparty hints.
- Candidate request summary.
- Candidate request positions.
- Source references and confidence notes.
- Questions for manager review.

Not allowed:

- Create approved business data directly.
- Choose final catalog products.
- Write to business tables.
- Calculate prices, VAT, totals, or legal document values.
- Create final invoices, commercial proposals, or PDFs.

### Tender Reader Mode For Mail Reader Agent

Readiness: target / documented mode, not implemented yet. Detailed rules are defined in [Tender Reader Rules](TENDER_READER_RULES.md).

Purpose:

- Process tender notification emails from a controlled tender folder or backend-provided input.
- Extract candidate tender metadata.
- Classify tender relevance as candidate `keep`, `skip`, `needs_review`, or `blocked_irrelevant`.
- Explain why a tender is likely relevant, ambiguous, or irrelevant.
- Produce manager questions and recommended next action.

Allowed outputs:

- Candidate tender metadata.
- Candidate tender classification.
- Product/category/manufacturer hints.
- Buyer, platform, URL/ID, region, and deadline candidates.
- Reason summary, matched rules, and source fragments.
- Manager questions and recommended next action.

Not allowed:

- Make final keep/skip/escalate decision.
- Submit tender bids.
- Generate final bid/offer documents.
- Generate КП, PDF, invoice, or 1C documents.
- Calculate prices, VAT, totals, margin, or delivery.
- Confirm SKU/catalog item.
- Scrape tender sites.
- Download tender documents.
- Access mailbox credentials or secrets directly.
- Trigger supplier quote, commercial offer, or document workflows without backend/manager action.

Rules:

- Tender Reader output is candidate data only.
- Backend/rules/manager workflow owns final tender status.
- Ambiguous cases should prefer `needs_review` over guessing.
- Final tender participation decision is outside LLM ownership.

### Future Tender Monitor Agent

Readiness: future boundary / not implemented yet.

Tender Reader mode may later become a separate Tender Monitor Agent if tender volume, platform coverage, deadline monitoring, scheduling, deduplication, document downloading, or filter complexity grows.

Future Tender Monitor Agent would still not own final business truth. It must not submit bids, generate КП/PDF/1C documents, calculate prices, scrape platforms without an approved integration boundary, or bypass backend validation and manager review.

### CRM Position Intent Agent / Product Selector Agent

Readiness: existing / available as model/logic; requires future quality testing and possible rework.

Purpose:

- Help a manager structure a request position.
- Normalize rough item descriptions into candidate intent.
- Suggest attributes, units, and clarification questions.
- Produce search hints for Backend Catalog Matcher.

Allowed outputs:

- Candidate item intent.
- Candidate attributes and unit hints.
- Suggested clarification questions.
- Candidate search hints for backend catalog matching.

Not allowed:

- Make the final catalog decision.
- Approve a CatalogItem.
- Calculate commercial terms, prices, VAT, or totals.
- Bypass Backend Catalog Matcher.

Quality note:

- The current Product Selector Agent result does not satisfy the product owner and must be evaluated before relying on automation.
- Evaluation categories, pass/fail rules, and fixture conversion guidance are defined in [Product Selector Agent Quality Evaluation Plan](PRODUCT_SELECTOR_EVAL.md).

### Client Catalog Assistant

Readiness: target / not implemented yet.

Purpose:

- Help a customer collect a basket through the published catalog.
- Ask clarifying questions using public catalog information.
- Explain published catalog options in customer-friendly language.

Allowed outputs:

- Candidate basket items.
- Clarification questions.
- Public catalog explanations.

Not allowed:

- Access internal catalog data, pricing rules, secrets, 1C, mail, or databases directly.
- Propose hidden, archived, or unverified catalog items.
- Approve catalog matches for internal CRM.
- Submit a request without customer confirmation.
- Generate final invoices, commercial proposals, or PDFs.

### Manager Catalog Assistant

Readiness: target / not implemented yet.

Purpose:

- Help a manager search and understand catalog candidates.
- Explain why candidates may match.
- Suggest analogs and clarifying questions.
- Summarize differences between candidates.

Allowed outputs:

- Candidate explanations.
- Candidate analog notes.
- Clarifying questions.
- Non-authoritative ranking assistance.

Not allowed:

- Replace Backend Catalog Matcher.
- Approve critical mismatches.
- Write final catalog links directly.
- Calculate prices, VAT, totals, or document values.

### Response Draft Agent

Readiness: target / not implemented yet.

Purpose:

- Prepare draft text for a response to the customer.
- Prepare an accompanying letter.
- Explain selected candidates in natural language.
- Prepare clarification questions.
- Draft a message for the manager.

Allowed outputs:

- Customer response draft text.
- Cover letter text.
- Explanation text for selected products.
- Clarification questions.
- Internal manager message text.

Strictly not allowed:

- Calculate sums.
- Calculate VAT.
- Set prices.
- Validate or fill legal requisites.
- Calculate totals or amount in words.
- Create final invoice PDF.
- Create final commercial proposal PDF.
- Send email directly.
- Produce final financial or legal document values.

Response Draft Agent may reference already approved values for wording, but the backend remains the source of truth for all amounts, requisites, positions, articles, prices, VAT, totals, delivery terms, signatures, seals, print templates, PDFs, and send workflow.

## Backend-Only Service Map

### Backend Catalog Matcher

Readiness: target backend service / not implemented yet.

Backend Catalog Matcher is a backend service, not a pure LLM agent.

Purpose:

- Perform final validation of position intent against the structured catalog.
- Score candidates.
- Detect critical mismatches.
- Mark analog candidates.
- Decide whether a position needs manager review.

Why it is not a pure LLM:

- It uses structured catalog data and deterministic validation rules.
- It must enforce business constraints and auditability.
- It controls final match status and prevents invalid catalog links.
- LLM assistance may explain or rank candidates, but backend matching rules decide whether a candidate can be approved.

Outputs:

- Candidate CatalogItem references.
- Score or rank.
- Critical mismatch flags.
- Analog flags.
- `needs_review` decision.
- Validation errors and explanation fields safe for UI.

### Agent Orchestrator

Readiness: target backend-only service / not implemented yet.

Purpose:

- Start agent workflows.
- Route controlled backend inputs to agent roles.
- Manage pipeline sequence and state.
- Create and update AgentRun records.
- Prevent frontend from calling Ollama directly.

### Agent Validation Service

Readiness: target backend-only service / not implemented yet.

Purpose:

- Validate LLM JSON/schema output.
- Normalize candidate data.
- Reject malformed, incomplete, unsafe, or contradictory agent output.
- Produce validation errors and review flags.
- Ensure candidate data does not become business data without backend validation.

### Invoice/PDF Generator

Readiness: target backend-only generator/template/script / not implemented yet.

Purpose:

- Generate invoices, commercial proposals, PDFs, and printable documents through deterministic backend templates or scripts.
- Use only confirmed data from approved/validated entities.
- Calculate sums, VAT, totals, amount in words, and document values in backend code.

Strict rule:

- LLM must never generate final invoice, commercial proposal, or PDF as the source of truth.
- LLM must never calculate financial values, legal requisites, prices, VAT, totals, amount in words, delivery terms, signatures, seals, or print-form values.

### Document Template Service

Readiness: target backend-only service / not implemented yet.

Purpose:

- Own templates for letters, invoices, commercial proposals, print forms, and accompanying documents.
- Render deterministic document structure from approved backend data.
- Keep final document generation auditable and reproducible.

## LLM and Backend Responsibility Boundary

LLM agents may:

- Extract candidate fields.
- Suggest structure.
- Suggest catalog search hints.
- Extract tender metadata.
- Suggest candidate tender classification.
- Explain candidates.
- Draft customer-facing text.
- Draft manager-facing text.
- Ask clarification questions.

LLM agents must not:

- Save approved business data directly.
- Make final catalog decisions.
- Make final tender keep/skip/escalate decisions.
- Scrape tender sites or download tender documents.
- Submit bids.
- Calculate financial values.
- Validate legal requisites.
- Generate final invoices, commercial proposals, or PDFs.
- Access mail, 1C, databases, secrets, or internal catalog storage directly.
- Send customer emails directly.

Backend services must:

- Validate all agent outputs.
- Decide whether data is approved, rejected, or needs review.
- Own catalog matching and document generation boundaries.
- Own final tender workflow state through rules and manager decisions.
- Persist only validated/approved business data.
- Record AgentRun audit trails.
- Protect secrets and backend-only integrations.

Managers may:

- Approve or reject candidate data.
- Confirm, skip, or override candidate tender classification.
- Choose among backend-validated catalog candidates.
- Edit draft text before sending.
- Decide when ambiguous positions or tenders remain in `needs_review`.

## Document and Invoice Generation Boundary

Invoices, commercial proposals, and PDFs are generated by backend-only generators using deterministic templates/scripts and confirmed data.

Confirmed document data includes:

- Counterparty.
- Legal requisites.
- Request positions.
- Catalog articles.
- Quantity.
- Price.
- VAT.
- Totals.
- Amount in words.
- Delivery terms.
- Signatures and seals.
- Print-form template.

Data sources:

- Approved RequestCard.
- Approved RequestPosition.
- Approved CatalogItem match.
- Validated Counterparty and Deal data.
- Backend-calculated financial values.

Positions with conflicts, critical mismatch, unresolved catalog match, or low-confidence extraction must remain in `needs_review` and must not enter final document generation.

Response Draft Agent may prepare only accompanying text, explanations, and clarification questions. It may not create final PDFs, calculate any financial/legal values, or send email directly.

Tender Reader may not create final bid documents, quote documents, PDF/Excel exports, invoices, or 1C records.

## AgentRun Audit and Trace Boundary

AgentRun is the single audit and trace contour for agent workflows. Full AgentRun schema, validation error taxonomy, prompt/model versioning, retry/fallback rules, and quality loop are defined in [AgentRun Schema and Quality Policy](AGENT_RUN.md).

AgentRun records should be used for:

- Mail Reader Agent runs.
- Tender Reader mode runs.
- CRM Position Intent Agent / Product Selector Agent runs.
- Client Catalog Assistant runs when introduced.
- Manager Catalog Assistant runs when introduced.
- Response Draft Agent runs when introduced.
- Optional LLM-assisted catalog explanation or ranking runs.

AgentRun fields used by the platform:

- `agent_name` and `agent_type` - agent identity for audit and reporting.
- `agent_version`, `mode`, `mode_version`, and `prompt_version` - versioning for quality comparisons.
- `model_name` - configured Ollama/API model name, not a filesystem model path.
- `model_provider` / `runtime` - runtime provider such as Ollama.
- `input_hash` - hash of controlled backend input for traceability and deduplication.
- `raw_response_reference` - reference to original LLM response retained according to policy and redaction rules.
- `normalized_response` - backend-normalized candidate data.
- `confidence` - agent-provided or backend-derived confidence marker.
- `validation_errors` - schema, safety, business, or consistency validation errors.
- `filter_version` - tender filtering rule version when Tender Reader mode is used.
- `retry_count`, `review_decision`, and `review_comment` - quality loop and fallback trace fields.

Security note:

- AgentRun records must not expose secrets, mail credentials, tokens, private keys, full prompts with sensitive data, sensitive customer data, tender buyer data beyond policy, or model paths to the frontend.

## Deferred Implementation

This document does not add:

- Backend code.
- Frontend code.
- FastAPI or React skeleton.
- Podman or Docker Compose files.
- PostgreSQL or Redis configuration.
- SQL, ORM, or migrations.
- Runtime dependencies.
- Email connector implementation.
- Tender folder integration.
- Tender-site scraping.
- Tender platform integration.
- Scheduler or backend jobs.
- Ollama/model changes.
- `.env.example` changes.

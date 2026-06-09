# ArtCRM AgentRun Schema and Quality Policy

This document fixes the conceptual AgentRun schema, validation error taxonomy, prompt/model versioning policy, retry/fallback rules, and quality loop before backend implementation begins. It does not define SQL, ORM models, migrations, API routes, FastAPI code, frontend code, containers, Redis, PostgreSQL, or runtime dependencies.

Agent-specific JSON/DTO output contracts are defined in [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md).

## Core Principles

- Every LLM agent run produces candidate data, not trusted business data.
- Backend validates every agent response before it can affect RequestCard, RequestPosition, CatalogItem, Deal, Project, documents, or 1C exchange workflows.
- AgentRun is the audit and quality-control record for each agent workflow execution.
- Agent failures must not block the entire RequestCard. Failed or ambiguous output should move the affected data into `needs_review` with safe fallback behavior.
- `model_name` is an Ollama/API model name, not a filesystem path to a model file.
- Error summaries must not expose secrets, full prompts, mail credentials, tokens, private keys, model paths, or sensitive customer data.

## Conceptual AgentRun Schema

### Identity and Agent Metadata

- `id` - stable AgentRun identifier.
- `agent_name` - human-readable agent role, such as Mail Reader Agent or Response Draft Agent.
- `agent_type` - normalized type, such as `mail_reader`, `position_intent`, `manager_catalog_assistant`, `client_catalog_assistant`, or `response_draft`.
- `agent_version` - implementation/configuration version of the agent workflow.
- `prompt_version` - version of the prompt or instruction pack.
- `model_name` - configured Ollama/API model name, never a filesystem model path.
- `model_provider` / `runtime` - runtime provider, for example `ollama`.

### Input References

- `input_reference` - backend-controlled reference to the input source.
- `input_hash` - hash of canonicalized backend input for deduplication, traceability, and quality comparisons.
- `request_card_id` - optional RequestCard reference.
- `request_position_id` - optional RequestPosition reference.

### Execution Status

- `status` - lifecycle status from the AgentRun status list.
- `retry_count` - number of controlled retries already attempted.
- `started_at` - run start timestamp.
- `finished_at` - run finish timestamp.
- `created_by` / `triggered_by` - backend workflow, manager, or system actor that started the run.

### Outputs and Validation

- `raw_response_reference` - reference to raw model output retained according to storage and redaction policy.
- `normalized_response` - backend-normalized candidate data after parsing and schema checks.
- `validation_status` - validation outcome, such as not_validated, valid, invalid, partial, or needs_review.
- `validation_errors` - list of validation error codes and safe details.
- `confidence` - confidence marker supplied by the agent, derived by backend validation, or both.

### Human Review

- `reviewed_by` - manager or reviewer who reviewed candidate data.
- `review_decision` - approved, rejected, corrected, needs_more_info, or deferred.
- `review_comment` - safe human review note without secrets or sensitive data beyond what is allowed for business audit.

## AgentRun Statuses

- `queued` - run is scheduled but not started.
- `running` - backend is executing the workflow.
- `completed` - agent returned output and backend completed initial parsing.
- `failed` - execution failed before usable candidate data was produced.
- `needs_review` - candidate data exists but backend or manager review is required.
- `rejected` - output is rejected and must not affect business entities.
- `approved` - output is accepted as validated candidate support for downstream entity changes.
- `archived` - run is retained for audit but removed from active queues.

Status notes:

- `completed` does not mean business-approved. It means execution completed and output can be validated.
- `approved` means backend validation and required human review have accepted the output for its intended use.
- `failed` or `rejected` must not block the entire RequestCard by default.

## Validation Error Taxonomy

### Schema and Structure Errors

- `invalid_json` - model output cannot be parsed as required JSON or structured format.
- `missing_required_field` - required field is absent.
- `unexpected_field` - output contains a field outside the allowed schema.
- `invalid_enum` - field value is not one of the allowed values.

### Business Candidate Errors

- `invalid_quantity` - quantity is absent, non-numeric, negative, zero when not allowed, or otherwise invalid.
- `invalid_unit` - unit is missing, unknown, unsupported, or inconsistent with the position.
- `low_confidence` - confidence is below the threshold for automatic acceptance.
- `ambiguous_position` - candidate position can map to multiple meanings or catalog branches.
- `critical_mismatch` - candidate data conflicts with structured catalog or business constraints.

### Safety and Runtime Errors

- `unsafe_content` - output contains unsafe, secret-like, sensitive, or policy-violating content.
- `timeout` - agent runtime did not respond within the allowed time.
- `ollama_unavailable` - Ollama or configured AI runtime is unavailable.
- `validation_exception` - backend validation failed due to an internal validation exception.

## Prompt and Model Versioning Policy

- Every agent must have `agent_version` and `prompt_version`.
- Every run must record `model_name` and `model_provider` / `runtime`.
- `model_name` must be a configured Ollama/API model name, not a file path.
- Prompt text must not contain secrets, tokens, passwords, API keys, mail credentials, private keys, or model paths.
- `prompt_version` must be stable enough to compare quality between versions.
- Prompt/model changes must enter the audit and quality loop before being considered successful.
- Quality reports should group results by `agent_name`, `agent_type`, `agent_version`, `prompt_version`, `model_name`, and `validation_errors`.
- Model or prompt changes that increase `low_confidence`, `invalid_json`, `critical_mismatch`, or manager corrections should be treated as quality regressions until reviewed.

## Retry and Fallback Policy

- Allow one controlled retry for `invalid_json` or temporary runtime failures such as `timeout` or `ollama_unavailable`.
- Retry must use the same controlled backend input reference and must create or update traceable AgentRun metadata.
- Do not retry indefinitely.
- If the retry fails, use safe fallback and move affected candidate data to `needs_review`.
- Agent errors should not block the entire RequestCard unless backend workflow rules later define a critical blocker.
- For RequestPosition extraction or matching assistance failures, keep the affected position in `needs_review` while the rest of the RequestCard can continue if valid.
- For Response Draft Agent failure, allow the manager to write the response manually.
- Error summaries must be redacted and must not expose secrets, full prompts, sensitive mail content, tokens, credentials, private keys, model paths, or raw internal stack traces.

## Quality Loop

- A manager can mark that the agent made a mistake.
- Manager corrections must be retained as reference examples when allowed by retention and privacy policy.
- AgentRun must link to the quality review decision or correction reference.
- Quality review should capture expected value, actual candidate value, correction reason, and reviewer identity where appropriate.
- Future reports should show quality by `agent_name`, `agent_type`, `prompt_version`, `model_name`, validation error code, review decision, and correction frequency.
- Repeated errors should produce candidates for prompt updates, validation rule updates, catalog normalization work, or training/evaluation sets.

## Security and Redaction Rules

- Store raw responses by reference, not necessarily inline, so retention and redaction can be controlled.
- Redact secrets and sensitive data before exposing any AgentRun details to the frontend.
- Error summaries must be safe for UI and PR/issue comments.
- Full prompts must not be exposed to frontend users by default.
- Internal prompts must not contain secrets.
- AgentRun must not store or expose filesystem model paths.

## Relationship to JSON Schemas

- LLM-agent outputs use the shared envelope and agent-specific payloads defined in `AGENT_JSON_SCHEMAS.md`.
- Backend-service outputs are decision/validated outputs, not LLM candidate outputs.
- AgentRun stores normalized LLM output after backend parsing and validation.
- Backend service execution records should link to AgentRun records when they consume LLM candidate data.

## Relationship to Business Entities

- AgentRun may propose changes to RequestCard and RequestPosition.
- AgentRun may support catalog explanation or ranking, but Backend Catalog Matcher owns final catalog validation.
- AgentRun may produce Response Draft Agent text, but final sending remains a manager/backend workflow decision.
- AgentRun output never writes directly into approved business entities without backend validation.

## Deferred Implementation Decisions

The following decisions are intentionally deferred:

- Physical database schema.
- Machine-enforced JSON schema files.
- API request/response DTO classes.
- Storage backend for raw responses.
- Retention policy and redaction implementation.
- Quality report UI.
- Prompt registry storage mechanism.
- Exact thresholds for confidence and retry behavior.

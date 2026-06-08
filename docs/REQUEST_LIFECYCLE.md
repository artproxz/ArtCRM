# ArtCRM Request Lifecycle

This document defines conceptual lifecycle states for RequestCard, RequestPosition, and AgentRun before backend implementation begins. It does not define code, database schema, ORM models, migrations, queues, or API routes.

Lifecycle states are backend-owned. The frontend may request transitions, but backend validation decides whether a transition is allowed.

## Shared State Vocabulary

The following states are used across ArtCRM request workflows. Not every state applies to every entity.

### incoming

A source item has entered the system but has not been parsed or turned into structured candidate data.

Typical use:

- RequestCard: source mail is available for intake.
- RequestPosition: usually not applicable because positions do not exist before parsing.
- AgentRun: run has not started yet; use queued or running internally if implementation later needs finer states.

### parsed

Source content has been processed and candidate fields are available, but they are not yet trusted business data.

Typical use:

- RequestCard: mail content has candidate request-level fields.
- RequestPosition: line items have candidate fields from mail parsing.
- AgentRun: output has been produced and awaits validation.

### draft

A backend-controlled draft exists and can be reviewed or edited before approval.

Typical use:

- RequestCard: draft card exists with candidate fields.
- RequestPosition: draft position exists with candidate item data.
- AgentRun: not usually applicable; AgentRun output may create drafts but the run itself is not edited as a draft.

### needs_review

Backend validation found missing, ambiguous, low-confidence, or conflicting data that requires operator review.

Typical use:

- RequestCard: request-level fields or counterparty identity require review.
- RequestPosition: quantity, unit, item name, attributes, or match candidate require review.
- AgentRun: output validation failed partially or requires operator decision.

### ready_for_matching

Entity has enough validated information to start catalog matching.

Typical use:

- RequestCard: all required positions are valid enough for matching workflow.
- RequestPosition: item name, quantity, unit, and attributes are sufficient for matching.
- AgentRun: not applicable as a lifecycle state; an AgentRun may trigger matching but is not matched itself.

### matched

A catalog match candidate has been selected or confidently proposed, but final approval may still be pending.

Typical use:

- RequestCard: all required positions have match candidates or approved matches.
- RequestPosition: catalog candidate exists and is available for review or approval.
- AgentRun: not applicable except as metadata about a matching run result.

### approved

Data has passed backend validation and required operator approval. Approved data may be used by CRM, documents, and future 1C exchange workflows.

Typical use:

- RequestCard: card is validated and ready for CRM workflow.
- RequestPosition: position and catalog link are approved.
- AgentRun: output has been validated and accepted as a source for approved or draft data.

### rejected

Data, candidate output, or transition was rejected and must not be used as authoritative business data.

Typical use:

- RequestCard: request should not proceed.
- RequestPosition: line item or match candidate is rejected.
- AgentRun: output failed validation or operator review.

### archived

Entity is removed from active workflow but retained for traceability according to retention policy.

Typical use:

- RequestCard: closed historical request.
- RequestPosition: historical or obsolete position.
- AgentRun: historical run retained for audit.

## RequestCard Lifecycle

RequestCard represents the request-level workflow created from incoming mail and operator review.

### Applicable States

- incoming
- parsed
- draft
- needs_review
- ready_for_matching
- matched
- approved
- rejected
- archived

### Typical Transitions

1. incoming -> parsed
   Backend mail intake selects a source message and Mail Reader Agent produces candidate request-level data.

2. parsed -> draft
   Backend validates the candidate schema enough to create a RequestCard draft.

3. draft -> needs_review
   Backend finds missing or ambiguous counterparty, subject, source references, positions, or required fields.

4. needs_review -> draft
   Operator edits candidate data and backend accepts the correction as a draft update.

5. draft -> ready_for_matching
   Backend confirms required request-level fields and position drafts are valid enough for catalog matching.

6. ready_for_matching -> matched
   Required positions have match candidates or approved catalog links.

7. matched -> approved
   Backend validates the complete request and operator approves business-critical values.

8. draft -> rejected, needs_review -> rejected, or matched -> rejected
   Operator or backend rejects the request with a reason.

9. approved -> archived or rejected -> archived
   RequestCard is retained for history but removed from active workflow.

### Guardrails

- Backend must reject invalid transitions.
- AI-extracted fields remain candidate data until backend validation.
- RequestCard cannot become approved while required RequestPositions are unresolved.
- Archived RequestCards must not be modified except by explicit administrative workflow.

## RequestPosition Lifecycle

RequestPosition represents one extracted line item from a RequestCard.

### Applicable States

- parsed
- draft
- needs_review
- ready_for_matching
- matched
- approved
- rejected
- archived

The incoming state usually does not apply because a RequestPosition does not exist before mail parsing creates candidate line item data.

### Typical Transitions

1. parsed -> draft
   Backend validates candidate position shape enough to create a draft position.

2. draft -> needs_review
   Backend detects missing quantity, unknown unit, unclear item name, conflicting attributes, or low-confidence extraction.

3. needs_review -> draft
   Operator edits candidate fields and backend accepts the correction as draft data.

4. draft -> ready_for_matching
   Backend confirms the position has enough validated data for catalog matching.

5. ready_for_matching -> matched
   Catalog Matching API returns one or more candidate CatalogItem matches.

6. matched -> approved
   Operator selects a candidate and backend validates the selected CatalogItem relationship.

7. draft -> rejected, needs_review -> rejected, ready_for_matching -> rejected, or matched -> rejected
   Operator or backend rejects the position or candidate match with a reason.

8. approved -> archived or rejected -> archived
   Position is retained for traceability but removed from active workflow.

### Guardrails

- RequestPosition cannot move to ready_for_matching until backend validates required matching inputs.
- Catalog candidates are not approved data until backend validates and records approval.
- Rejected candidates must not be used by CRM, documents, pricing, stock, or 1C exchange.
- Position updates may require RequestCard lifecycle recalculation.

## AgentRun Lifecycle

AgentRun represents one AI-assisted backend workflow execution, such as Mail Reader Agent extraction or catalog matching assistance.

### Applicable States

- incoming
- parsed
- needs_review
- approved
- rejected
- archived

The draft, ready_for_matching, and matched states usually apply to RequestCard and RequestPosition rather than AgentRun. If future implementation needs operational run states, it may add queued, running, succeeded, or failed as technical statuses while preserving the validation lifecycle described here.

### Typical Transitions

1. incoming -> parsed
   Backend starts an agent run from controlled input and receives structured candidate output.

2. parsed -> needs_review
   Backend validation finds malformed, incomplete, low-confidence, or ambiguous output.

3. parsed -> approved
   Backend validates the output and accepts it as a source for draft or approved domain data.

4. needs_review -> approved
   Operator review resolves the issue and backend validates the final candidate data.

5. parsed -> rejected or needs_review -> rejected
   Backend or operator rejects the output.

6. approved -> archived or rejected -> archived
   AgentRun is retained for audit and removed from active review queues.

### Guardrails

- AgentRun output is never authoritative business data by itself.
- Backend must validate response shape before exposing output to downstream workflows.
- AgentRun errors must not expose secrets, mail credentials, tokens, private keys, model paths, or full internal prompts in UI or logs.
- An approved AgentRun can support draft or approved data, but the target entity still owns its own lifecycle.

## Cross-Entity Lifecycle Rules

- A RequestCard may depend on RequestPosition states before it can move to ready_for_matching, matched, or approved.
- A RequestPosition may depend on Catalog Matching API output before it can move to matched or approved.
- An AgentRun may produce candidate data for RequestCard and RequestPosition, but it does not bypass backend validation.
- Rejected AgentRun output must not automatically reject the RequestCard unless backend workflow rules explicitly decide that later.
- Archived records are historical and should not be reused as active candidate data.

## Deferred Lifecycle Decisions

The following decisions are intentionally deferred:

- Concrete enum names in code.
- Database storage of lifecycle states.
- Audit event schema.
- Permission matrix for state transitions.
- UI labels and localization.
- SLA and timeout behavior.
- Reopen and restore policies for archived records.

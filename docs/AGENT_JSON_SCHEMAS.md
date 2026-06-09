# ArtCRM Agent JSON Schemas and DTO Contracts

This document fixes conceptual JSON schemas and DTO contracts for data exchange between LLM agents, backend validation, backend-only services, and future APIs. It is documentation only. It does not add backend code, frontend code, FastAPI, React, containers, PostgreSQL, Redis, SQL, ORM, migrations, dependencies, secrets, model paths, or real customer data.

## Core Contract Rules

- LLM-agent output is candidate data.
- Backend-service output is validated data or decision data.
- Every LLM output must pass backend validation before it affects RequestCard, RequestPosition, CatalogItem, Deal, documents, or 1C exchange.
- Shared LLM Agent Output Envelope is mandatory for all LLM-agent outputs.
- Envelope fields are shared, but `payload` differs by agent.
- `schema_version` is required for every output.
- `raw_response` must not be written directly into business tables.
- `normalized_response` is stored through AgentRun after backend parsing and validation.
- Every LLM output must be linked to AgentRun.
- Every backend-service output must be linked to a backend service execution record, and may also reference AgentRun records that produced candidate inputs.
- `model_name` is an Ollama/API model name, not a filesystem model path.
- Outputs must not contain secrets, credentials, tokens, private keys, model paths, full prompts, or real customer data in examples.

## Component Readiness Status

### Existing / Available But Documented As Contracts

- Mail Reader Agent: generally exists as model/logic, but its JSON contract is formally fixed here.
- Product Selector Agent / CRM Position Intent Agent: generally exists as model/logic, but current result is not accepted by the product owner. It requires separate future quality testing and possible rework.

### Target / Not Implemented Yet

- Client Catalog Assistant: target future LLM for customer catalog page.
- Manager Catalog Assistant: target future LLM for manager catalog assistance.
- Response Draft Agent: target future LLM for customer response drafts.
- Backend Catalog Matcher: target backend service, not LLM.
- Invoice/PDF Generator: target backend-only generator/template/script.
- Agent Orchestrator: target backend-only service.
- Agent Validation Service: target backend-only service.
- Document Template Service: target backend-only service.

This document describes contracts and target boundaries. It must not be read as proof that all listed agents or services are already implemented.

## Shared LLM Agent Output Envelope

All LLM agents must return a common envelope. Backend validation uses the envelope consistently, while each agent-specific `payload` follows its own schema.

```json
{
  "schema_version": "agent-output.v1",
  "agent_name": "mail_reader_agent",
  "agent_role": "mail_reader",
  "output_type": "mail_reader_result",
  "status": "completed",
  "confidence": 0.82,
  "source_refs": [
    {
      "type": "mail_message",
      "id": "demo-mail-ref",
      "field": "body"
    }
  ],
  "payload": {},
  "validation_hints": [
    {
      "code": "low_confidence",
      "field": "payload.clean_products[0].unit",
      "message": "Unit requires backend validation"
    }
  ],
  "next_action": "backend_validation"
}
```

### Envelope Fields

- `schema_version` - required schema version for compatibility checks.
- `agent_name` - concrete agent name used for audit and quality reports.
- `agent_role` - normalized role such as mail_reader, position_intent, client_catalog_assistant, manager_catalog_assistant, or response_draft.
- `output_type` - specific output contract type.
- `status` - agent output status, such as completed, partial, needs_review, or failed.
- `confidence` - overall confidence marker. It is not enough for business approval.
- `source_refs` - references to backend-controlled source inputs.
- `payload` - agent-specific candidate data.
- `validation_hints` - non-authoritative hints for backend validation.
- `next_action` - suggested next step, such as backend_validation, manager_review, customer_confirmation, or safe_fallback.

### Envelope Validation Rules

- Backend rejects missing `schema_version`.
- Backend validates `agent_role` and `output_type` against allowed values.
- Backend treats `confidence` as a hint, not as approval.
- Backend validates `source_refs` against controlled backend references.
- Backend validates the agent-specific `payload` before use.
- Backend stores normalized output through AgentRun.
- Backend rejects or redacts any output containing secrets, credentials, tokens, private keys, model paths, full prompts, or unsafe sensitive data.

## Mail Reader Agent Output

Readiness: existing / available as model/logic, contract formalized in this document.

Purpose:

- Process dirty incoming email.
- Produce candidate clean request data.
- Prepare data for backend validation, RequestCard creation, and RequestPosition draft creation.

Important boundaries:

- Does not choose final catalog products.
- Does not calculate prices.
- Does not create final RequestCard without backend validation.
- Output goes to backend validation, then RequestCard and RequestPosition[] drafts.

Payload schema:

```json
{
  "clean_customer_request": "Customer asks for a demo set of devices with unclear details.",
  "manager_summary": "Customer request needs product clarification before catalog matching.",
  "mail_type": "new_request",
  "next_action": "create_request_card_draft",
  "clean_products": [
    {
      "source_text": "demo product line from email",
      "normalized_text": "demo product candidate",
      "quantity": 2,
      "unit": "pcs",
      "notes": "Requires backend validation and later position intent parsing"
    }
  ],
  "customer_context": {
    "sender_name": "Demo Customer",
    "company_hint": "Demo Company",
    "contact_email_ref": "source_ref:sender_email",
    "language": "ru"
  },
  "attachments_summary": [
    {
      "attachment_ref": "demo-attachment-ref",
      "summary": "Attachment may contain product details",
      "requires_review": true
    }
  ]
}
```

Downstream consumer:

- Backend validation layer validates the envelope and payload.
- Valid candidate fields create RequestCard draft and RequestPosition drafts.
- Ambiguous or low-confidence fields move to `needs_review`.

## CRM Position Intent Agent / Product Selector Agent Output

Readiness: existing / available as model/logic, but requires future quality testing and possible rework because the product owner is not satisfied with the current result.

Evaluation plan: quality categories, synthetic examples, pass/fail criteria, and future fixture conversion guidance are defined in [Product Selector Agent Quality Evaluation Plan](PRODUCT_SELECTOR_EVAL.md).

Purpose:

- Parse one concrete position.
- Convert rough text into structured intent.
- Produce search hints for Backend Catalog Matcher.

Input context:

- One concrete position source text.
- `clean_customer_request` from Mail Reader Agent.
- `manager_summary` from Mail Reader Agent.
- Full normalized JSON output of Mail Reader Agent as backend-controlled context.

Important boundaries:

- Returns structured intent, not a final CatalogItem.
- Does not approve catalog matches.
- Does not bypass Backend Catalog Matcher.
- Output goes to backend validation, then Backend Catalog Matcher.

Payload schema:

```json
{
  "source_text": "demo raw position",
  "normalized_text": "demo normalized position",
  "intent": {
    "product_type": "demo_product_type",
    "manufacturer": "demo_manufacturer_or_unknown",
    "series": "demo_series_or_unknown",
    "model": "demo_model_or_unknown",
    "range": "demo_range_or_unknown",
    "connection": "demo_connection_or_unknown",
    "accuracy_class": "demo_accuracy_or_unknown",
    "material": "demo_material_or_unknown",
    "execution": "demo_execution_or_unknown",
    "options": ["demo_option"],
    "quantity": 1,
    "unit": "pcs"
  },
  "search": {
    "main_query": "demo catalog search query",
    "search_variants": [
      "demo variant 1",
      "demo variant 2"
    ]
  },
  "must_have": ["demo required parameter"],
  "forbidden_mismatch": ["demo critical mismatch"],
  "analog_request": {
    "allowed": false,
    "reason": "Customer did not explicitly allow analogs"
  },
  "needs_clarification": true,
  "clarification_questions": [
    "Please confirm the required connection type."
  ]
}
```

Downstream consumer:

- Backend validation validates intent fields and required parameters.
- Backend Catalog Matcher receives validated intent/search hints.
- Quality review must evaluate this agent separately before relying on automated usage.

## Client Catalog Assistant Output

Readiness: target / not implemented yet.

Purpose:

- Support customer-facing catalog search and cart drafting through published catalog data only.
- Help customer clarify missing parameters before submitting a request.

Important boundaries:

- Works only with published and moderated catalog data.
- Must not propose hidden, archived, or unverified items.
- Must not submit a request without customer confirmation.
- Analogs must be explicitly marked.
- Output goes to customer confirmation, then Cart, then backend validation, then RequestCard.

Payload schema:

```json
{
  "original_user_query": "demo customer catalog query",
  "recognized_parameters": {
    "product_type": "demo_product_type",
    "manufacturer": "unknown",
    "quantity": 1,
    "unit": "pcs"
  },
  "proposed_items": [
    {
      "public_catalog_item_ref": "demo-public-item-ref",
      "display_name": "Demo published item",
      "is_analog": false,
      "confidence": 0.74,
      "explanation": "Matches visible public parameters"
    }
  ],
  "missing_parameters": ["connection"],
  "clarification_questions": [
    "Which connection type do you need?"
  ],
  "cart_draft_items": [
    {
      "public_catalog_item_ref": "demo-public-item-ref",
      "quantity": 1,
      "unit": "pcs",
      "customer_note": "Pending confirmation"
    }
  ],
  "customer_confirmation_required": true
}
```

Downstream consumer:

- Customer confirms or edits cart draft.
- Backend validates submitted cart data.
- Validated cart data can create RequestCard and RequestPosition drafts.

## Manager Catalog Assistant Output

Readiness: target / not implemented yet.

Purpose:

- Help internal manager interpret Backend Catalog Matcher candidates.
- Explain candidates, mismatch reasons, analog rules, and follow-up actions.

Important boundaries:

- May see internal codes, match candidates, mismatch reasons, analog rules, and service data.
- Must not bypass Backend Catalog Matcher.
- Must not write `catalog_item_id` directly into business entities.
- Helps manager decide; backend validates and persists decisions.

Payload schema:

```json
{
  "position_summary": "Demo position requires manager decision",
  "candidate_analysis": [
    {
      "candidate_ref": "catalog-candidate-ref",
      "catalog_item_ref": "catalog-item-ref",
      "is_analog": true,
      "mismatch_reasons": ["demo mismatch reason"],
      "strengths": ["demo matching parameter"],
      "risks": ["demo risk"],
      "recommendation": "needs_manager_review"
    }
  ],
  "suggested_manager_actions": [
    "Ask customer to confirm material",
    "Reject analog unless customer accepts replacement"
  ],
  "clarification_question_to_customer": "Can we offer an analog with different material?",
  "reparse_instruction": "Re-run position intent after customer confirms material"
}
```

Downstream consumer:

- Manager reviews assistant output.
- Backend records manager decision.
- Backend Catalog Matcher and RequestPosition lifecycle remain source of truth.

## Response Draft Agent Output

Readiness: target / not implemented yet.

Purpose:

- Draft response text for customer communication.
- Draft accompanying text, explanations, clarification questions, and manager notes.

Important boundaries:

- Does not calculate sums, VAT, prices, requisites, totals, or amount in words.
- Does not generate final PDF.
- Does not send email directly.
- Attachments must reference documents generated by backend-only generator/template/script.
- Output goes to manager review, then backend send workflow.

Payload schema:

```json
{
  "subject": "Clarification for your request",
  "body_text": "Hello, please confirm the missing parameters before we prepare the offer.",
  "body_html": "<p>Hello, please confirm the missing parameters before we prepare the offer.</p>",
  "attachments_to_include": [
    {
      "document_ref": "backend-generated-document-ref",
      "document_type": "commercial_proposal_pdf",
      "required": false
    }
  ],
  "manager_notes": [
    "Check unresolved position before sending."
  ],
  "requires_manager_approval": true
}
```

Downstream consumer:

- Manager reviews and edits the draft.
- Backend send workflow sends approved response.
- Backend-only document generator creates any final invoice, commercial proposal, or PDF attachment.

## Backend Catalog Matcher Output

Readiness: target backend service / not implemented yet. This is backend-service output, not LLM output.

Purpose:

- Decide exact match, analog, needs_review, or no_match using validated position intent and structured catalog data.
- Enforce critical mismatch rules and prevent unsafe auto-apply.

Payload schema:

```json
{
  "match_status": "needs_review",
  "auto_apply_allowed": false,
  "final_decision": "review_required",
  "score": 0.68,
  "critical_checks": [
    {
      "check": "connection",
      "status": "mismatch",
      "expected": "demo_expected_connection",
      "actual": "demo_candidate_connection",
      "blocks_auto_apply": true
    }
  ],
  "candidates": [
    {
      "catalog_item_ref": "catalog-item-ref",
      "score": 0.68,
      "is_analog": true,
      "analog_reason": "Different connection type",
      "critical_mismatch": true,
      "explanation": "Candidate requires manager review"
    }
  ],
  "review_reason": "Critical parameter mismatch blocks automatic catalog assignment"
}
```

Decision rules:

- Backend decides exact match, analog, needs_review, or no_match.
- Critical mismatch blocks auto-apply.
- Analog must be explicitly marked.
- Backend output may reference LLM candidate data, but does not trust it without validation.

## Invoice/PDF Generator Output

Readiness: target backend-only generator/template/script / not implemented yet. This is not LLM output.

Purpose:

- Generate invoice, commercial proposal, and PDF metadata from approved/validated entities.
- Calculate financial values in backend code using deterministic templates/scripts.

Payload schema:

```json
{
  "invoice_id": "demo-invoice-id",
  "invoice_number": "DEMO-0001",
  "invoice_date": "2026-01-01",
  "currency": "RUB",
  "supplier": {
    "counterparty_ref": "supplier-ref",
    "legal_name": "Demo Supplier",
    "requisites_ref": "validated-supplier-requisites-ref"
  },
  "buyer": {
    "counterparty_ref": "buyer-ref",
    "legal_name": "Demo Buyer",
    "requisites_ref": "validated-buyer-requisites-ref"
  },
  "lines": [
    {
      "request_position_ref": "request-position-ref",
      "catalog_item_ref": "catalog-item-ref",
      "sku": "DEMO-SKU",
      "name": "Demo approved item",
      "quantity": 1,
      "unit": "pcs",
      "unit_price": "100.00",
      "vat_rate": "20%",
      "line_total": "120.00"
    }
  ],
  "totals": {
    "subtotal": "100.00",
    "vat": "20.00",
    "total": "120.00",
    "amount_words": "demo amount in words generated by backend"
  },
  "pdf": {
    "document_ref": "generated-pdf-ref",
    "template_version": "invoice-template.v1",
    "status": "generated"
  },
  "validation": {
    "status": "valid",
    "errors": []
  }
}
```

Decision rules:

- Uses only approved/validated entities.
- Backend calculates subtotal, VAT, total, and amount in words.
- PDF is generated by backend template/script.
- LLM may prepare only accompanying text, not legal or financial values.

## Cross-Schema Flow

1. LLM agent produces Shared LLM Agent Output Envelope.
2. Backend parses raw response and creates AgentRun trace.
3. Backend validates envelope and payload.
4. Backend stores `normalized_response` through AgentRun.
5. Candidate data updates draft entities only after validation allows it.
6. Backend-only services consume validated candidate data and produce decision outputs.
7. Manager approval is required where backend marks `needs_review`.
8. Approved backend decisions can update business entities.

## Cross-Schema Safety Rules

- All LLM outputs are candidate data.
- All LLM outputs must pass backend validation.
- Backend-service outputs are validated or decision data.
- `schema_version` is mandatory.
- `raw_response` must not directly enter business tables.
- `normalized_response` is stored through AgentRun.
- Output must not contain secrets, credentials, tokens, private keys, model paths, full prompts, or real customer data.
- Model is identified by `model_name`, never by filesystem path.
- Every LLM output is linked to AgentRun.
- Every backend-service output is linked to a backend service execution record.

## Deferred Implementation Decisions

The following decisions are intentionally deferred:

- Machine-enforced JSON Schema files.
- DTO class names and field types.
- FastAPI request/response models.
- Persistence schema.
- Validation implementation.
- Prompt execution code.
- Backend service execution record schema.
- UI rendering of schema validation errors.

# Backend Catalog Matcher API Contract

This document defines the documentation-only conceptual API and DTO contract for Backend Catalog Matcher in ArtCRM.

It does not add backend code, FastAPI routes, controllers, services, database schema, SQL, ORM, migrations, parser/import runner, API implementation, UI, tests, pricing logic, CP/invoice/PDF/1C flow, dependencies, containers, Ollama calls, model or Modelfile changes, `.env.example` changes, Excel files, real catalog rows, real stock rows, real prices, customer data, production emails, credentials, tokens, secrets, private keys, or filesystem model paths.

## Purpose

This document fixes the conceptual API and DTO contract for Backend Catalog Matcher so future backend implementation, Product Selector integration, and manager workflows use the same request and response structure.

This document is:

- a conceptual API/DTO contract;
- a boundary between Product Selector candidate data and backend catalog matching decisions;
- a schema reference for future backend service implementation;
- a documentation-only artifact.

This document is not:

- backend implementation;
- FastAPI route implementation;
- database schema;
- parser/import runner;
- UI;
- pricing, CP, invoice, PDF, or 1C implementation.

## API Boundary

Backend Catalog Matcher is a backend-only decision service. It receives backend-validated Product Selector candidate data and returns validated decision data.

Conceptual endpoint:

```text
POST /catalog/match
```

Conceptual service method:

```text
catalog.match_position
```

Boundary rules:

- do not implement the endpoint in this task;
- do not add FastAPI, router, controller, or service code;
- do not read raw Excel/source files inside the matcher request;
- do not call Ollama or any LLM;
- do not calculate prices or commercial totals;
- do not create CP, invoice, PDF, or 1C records;
- do not create confirmed request positions directly;
- only describe the contract for future implementation.

Request data is candidate data until matcher validation succeeds. Response data is backend decision data, but manager workflow may still require review depending on the decision.

## Request DTO

The request DTO identifies the request position, Product Selector output, normalized intent, candidate related components, analog request, catalog context, stock context, and audit metadata.

| Field | Required | Type | Meaning | Validation Note |
| --- | --- | --- | --- | --- |
| `schema_version` | required | string | DTO schema version. | Must match supported matcher API schema. |
| `request_id` | required | string | Unique matcher request ID. | Required for tracing and idempotency. |
| `idempotency_key` | required | string | Stable key for duplicate execution prevention. | Same normalized input and context should reuse stored result. |
| `request_position_ref` | required | string | Reference to request position candidate/workflow item. | Must not imply a confirmed business row unless created by separate workflow. |
| `request_card_ref` | optional | string | Reference to parent request card. | Useful for audit and manager context. |
| `agent_run_ref` | required | string | Reference to Product Selector AgentRun. | Must be present for audit linkage. |
| `product_selector_output_ref` | required | string | Reference to Product Selector output envelope. | Output must be backend-validated before matching. |
| `source_text` | optional | string | Original client line or manager-entered source text. | Must not contain secrets, credentials, full emails, or private files. |
| `normalized_text` | optional | string | Normalized text used by Product Selector/backend validation. | Used for audit and secondary search only. |
| `manufacturer_scope` | required | string | Manufacturer boundary, for example `ROSMA`. | Must be a supported manufacturer or return validation error. |
| `product_type` | required | string | Product type for profile selection. | Must exist in ProductTypeFilterProfile registry. |
| `product_kind` | required | string | Controlled product kind. | Must use controlled vocabulary from catalog docs. |
| `structured_intent` | required | object | Product-type-specific normalized intent. | Applicability is enforced by ProductTypeFilterProfile. |
| `must_have[]` | optional | array<object> | Explicit requirements that must be satisfied. | Field names must be applicable to product type. |
| `forbidden_mismatch[]` | optional | array<string> | Fields where mismatch blocks automatic matching. | Not-applicable fields cannot be required here. |
| `missing_fields[]` | optional | array<string> | Fields Product Selector/backend validation already found missing. | Matcher may add more missing fields after profile enforcement. |
| `related_component_suggestions[]` | optional | array<object> | Candidate related components from Product Selector or backend rules. | Candidate data only; requires matcher/backend validation. |
| `analog_request` | optional | object | Whether analog matching is requested or allowed. | Does not allow LLM-invented analogs. |
| `validation_hints` | optional | object | Backend validation notes from earlier pipeline stages. | Must not override matcher validation. |
| `catalog_publication_ref` | optional | string | Requested active catalog publication context. | If omitted, matcher uses current active publication. |
| `stock_snapshot_ref` | optional | string | Requested stock snapshot context. | If omitted, matcher uses latest published stock snapshot when applicable. |
| `locale` | optional | string | Response language/format hint. | Example: `ru-RU`; must not change decision logic. |
| `requested_at` | required | string | Request timestamp in ISO-8601 format. | Used for audit and freshness checks. |
| `requested_by_ref` | optional | string | User/service that requested matching. | Must not contain credentials. |

### Request Example

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "request_id": "matcher_request:demo-001",
  "idempotency_key": "matcher_request:demo-001:catalog-demo-active:stock-demo-latest",
  "request_position_ref": "request_position:demo-001",
  "request_card_ref": "request_card:demo-001",
  "agent_run_ref": "agent_run:demo-product-selector-001",
  "product_selector_output_ref": "agent_output:demo-product-selector-001",
  "source_text": "Demo pressure gauge line with hydrofilling request",
  "normalized_text": "pressure gauge TM-521R.00 0-1 MPa G1/2 accuracy 1.0 qty 5 hydrofilling glycerin",
  "manufacturer_scope": "ROSMA",
  "product_type": "pressure_gauge",
  "product_kind": "main_product",
  "structured_intent": {
    "model_candidate": "TM-521R.00",
    "series_candidate": "TM-521",
    "measurement_range": "0-1",
    "range_unit": "MPa",
    "thread": "G1/2",
    "connection_type": "radial",
    "accuracy_class": "1.0",
    "material": null,
    "execution": null,
    "options": [],
    "quantity": 5,
    "unit": "pcs",
    "case_diameter": 100,
    "temperature_range": null,
    "immersion_length": null,
    "stem_diameter": null,
    "signal_output": null,
    "hydrofilling_requested": true,
    "hydrofilling_fluid_type": "glycerin"
  },
  "must_have": [
    { "field": "measurement_range", "value": "0-1", "source": "product_selector" },
    { "field": "range_unit", "value": "MPa", "source": "product_selector" },
    { "field": "thread", "value": "G1/2", "source": "product_selector" },
    { "field": "accuracy_class", "value": "1.0", "source": "product_selector" }
  ],
  "forbidden_mismatch": [
    "measurement_range",
    "range_unit",
    "thread",
    "accuracy_class"
  ],
  "missing_fields": [],
  "related_component_suggestions": [
    {
      "relation_type": "service_position",
      "suggested_type": "hydrofilling",
      "suggested_model_candidate": "Hydrofilling with glycerin for pressure gauge diameter 100 - 5 pcs",
      "parent_position_ref": "request_position:demo-001",
      "quantity_policy": "same_as_parent",
      "quantity_candidate": 5,
      "requires_confirmation": true,
      "already_present_in_request": false,
      "backend_validation_required": true,
      "manufacturer_scope": "ROSMA",
      "compatibility_hints": {
        "parent_series_candidate": "TM-521",
        "fluid_type": "glycerin"
      },
      "question_to_manager": null
    }
  ],
  "analog_request": {
    "requested": false,
    "allowed_by_customer": false,
    "allowed_by_manager_policy": false,
    "source_text": null,
    "reason": null,
    "constraints": [],
    "forbidden_mismatch": []
  },
  "validation_hints": {
    "llm_output_is_candidate_data": true,
    "backend_validation_completed": true,
    "unsafe_content_detected": false
  },
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": "stock_snapshot:demo-rosma-latest-001",
  "locale": "ru-RU",
  "requested_at": "2026-06-10T09:00:00Z",
  "requested_by_ref": "user:demo-manager"
}
```

## Structured Intent DTO

`structured_intent` is product-type-specific. It is not a universal product schema where every field applies to every product.

Minimum conceptual fields:

| Field | Type | Meaning | Applicability Note |
| --- | --- | --- | --- |
| `model_candidate` | string/null | Candidate model name from Product Selector. | Optional helper for lookup/ranking. |
| `series_candidate` | string/null | Candidate series/family. | Can be derived or validated against catalog. |
| `measurement_range` | string/null | Pressure or measurement range. | Required for pressure products, not for all product types. |
| `range_unit` | string/null | Unit for measurement range. | Must match product profile. |
| `thread` | string/null | Connection thread. | Not applicable for some service positions. |
| `connection_type` | string/null | Radial, axial, process connection, or similar. | Critical only for applicable product types. |
| `accuracy_class` | string/null | Accuracy class candidate. | Not applicable to some accessories/services. |
| `material` | string/null | Material candidate. | Critical only when requested in `must_have`. |
| `execution` | string/null | Execution/version candidate. | Critical only when requested or profile requires it. |
| `options[]` | array<string> | Parsed options. | Optional unless profile requires an option. |
| `quantity` | number/null | Requested quantity. | Used for stock and related components; not price calculation. |
| `unit` | string/null | Quantity unit, for example `pcs`. | Must be normalized. |
| `case_diameter` | number/null | Gauge case diameter. | Not applicable to many non-gauge products. |
| `temperature_range` | string/null | Temperature range. | Required for thermometer/thermomanometer profiles. |
| `immersion_length` | number/null | Thermometer/thermowell immersion length. | Not applicable to pressure gauges. |
| `stem_diameter` | number/null | Thermometer/thermowell stem diameter. | Product-type-specific. |
| `signal_output` | string/null | Signal output for pressure transducer/relay-like products. | Required for pressure transducer. |
| `hydrofilling_requested` | boolean/null | Whether hydrofilling is requested. | Must be validated against parent series support. |
| `hydrofilling_fluid_type` | string/null | Fluid type such as glycerin or silicone. | Required if hydrofilling needs a confirmed fluid. |

Applicability rules are taken from `ProductTypeFilterProfile` in `docs/CATALOG_MODEL.md`. Fields marked `not_applicable` for a product type must not be used as required filters.

## Must Have / Forbidden Mismatch DTO

`must_have[]` is a list of explicit requirements extracted from Product Selector output, manager input, or backend validation.

Conceptual `must_have[]` item fields:

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `field` | required | string | Normalized field name. |
| `value` | required | string/number/boolean/array/null | Required value. |
| `source` | optional | string | Source of the requirement, for example `product_selector`, `manager`, or `backend_rule`. |
| `critical` | optional | boolean | Whether mismatch is expected to block automatic selection. |

`forbidden_mismatch[]` is a list of fields where mismatch blocks automatic matching.

Examples:

- `measurement_range`;
- `range_unit`;
- `thread`;
- `accuracy_class`;
- `signal_output`;
- `material`;
- `immersion_length`.

Rules:

- a field in `forbidden_mismatch[]` must be applicable to the selected `product_type`;
- not-applicable fields in `must_have[]` or `forbidden_mismatch[]` should produce `not_applicable_field_used_as_required`;
- Product Selector confidence must not override a forbidden mismatch.

## Related Component Suggestion DTO

`related_component_suggestions[]` contains candidate data only. A suggestion must not become a confirmed CP/invoice/request line without backend validation and manager workflow.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `relation_type` | required | string | Relationship type, for example `service_position`, `accessory`, or `suppressed_recommendation`. |
| `suggested_type` | required | string | Suggested component/service type. |
| `suggested_model_candidate` | optional | string/null | Human-readable candidate model/service text. |
| `parent_position_ref` | required | string | Parent position reference. |
| `quantity_policy` | required | string | Quantity policy, for example `same_as_parent` or `manual`. |
| `quantity_candidate` | optional | number/null | Candidate quantity. |
| `requires_confirmation` | required | boolean | Whether manager/customer confirmation is required. |
| `already_present_in_request` | optional | boolean | Whether the component already appears in the source request. |
| `backend_validation_required` | required | boolean | Must be true for Product Selector suggestions. |
| `manufacturer_scope` | optional | string/null | Manufacturer scope for validation. |
| `compatibility_hints` | optional | object | Parent compatibility hints. |
| `question_to_manager` | optional | string/null | Question if validation needs clarification. |

Rules:

- suggestions are candidate data only;
- duplicate suppression must be preserved;
- hydrofilling is a separate service-position candidate, not just a note;
- unsupported parent series may return `blocked` or `needs_review`.

## Analog Request DTO

`analog_request` describes whether analog matching is requested or allowed. It does not allow LLM-invented analogs.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `requested` | required | boolean | Whether analog matching is requested. |
| `allowed_by_customer` | optional | boolean | Whether customer allowed analogs. |
| `allowed_by_manager_policy` | optional | boolean | Whether internal policy allows analogs. |
| `source_text` | optional | string/null | Source phrase indicating analog request. |
| `reason` | optional | string/null | Why analog lookup is requested. |
| `constraints` | optional | array<object|string> | Constraints analog must satisfy. |
| `forbidden_mismatch` | optional | array<string> | Fields analog must not mismatch. |

Rules:

- analog can be returned only if validated analog layer has a rule/candidate;
- no LLM-invented analogs;
- analog result requires manager confirmation unless future policy explicitly allows automatic use.

## Response DTO

The response DTO is backend decision data. It must be machine-readable and include enough manager-facing context to explain the decision.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `schema_version` | required | string | Response DTO schema version. |
| `matcher_version` | required | string | Matcher implementation/rules version. |
| `request_id` | required | string | Echoes request ID. |
| `request_position_ref` | required | string | Echoes request position reference. |
| `decision` | required | string | Decision enum value. |
| `decision_reason` | required | string | Machine-readable/human-readable reason summary. |
| `decision_severity` | required | string | Severity such as `info`, `warning`, or `blocking`. |
| `selected_catalog_item_id` | optional | string/null | Selected catalog item ID if any. |
| `selected_display_name` | optional | string/null | Display name for manager review. |
| `selected_product_type` | optional | string/null | Product type of selected item. |
| `selected_manufacturer` | optional | string/null | Manufacturer of selected item. |
| `selected_series` | optional | string/null | Selected series. |
| `selected_model` | optional | string/null | Selected model. |
| `matched_fields[]` | required | array<object|string> | Fields that matched. |
| `mismatched_fields[]` | required | array<object|string> | Fields that mismatched. |
| `missing_fields[]` | required | array<object|string> | Missing fields requiring review/clarification. |
| `ignored_not_applicable_fields[]` | required | array<object|string> | Candidate fields ignored because profile marks them not applicable. |
| `rejected_candidates[]` | required | array<object> | Rejected catalog candidates and reasons. |
| `stock_status` | required | string | Stock status enum value. |
| `availability` | required | object | Stock/availability DTO. |
| `related_component_results[]` | required | array<object> | Validation results for related components. |
| `analog_result` | required | object | Analog result DTO. |
| `confidence` | required | number | Matcher confidence score from 0 to 1. |
| `manager_message` | required | string | Manager-facing explanation. |
| `clarification_questions[]` | required | array<string> | Questions for manager/customer. |
| `source_refs[]` | required | array<string> | Source references used for decision. |
| `audit_refs[]` | required | array<string> | Audit references for traceability. |
| `catalog_publication_ref` | required | string | Catalog publication used. |
| `stock_snapshot_ref` | optional | string/null | Stock snapshot used if applicable. |
| `next_action` | required | string | Suggested workflow action. |

## Decision Enum

Allowed `decision` values:

| Decision | automatic_use_allowed | manager_review_required | customer_clarification_required | Meaning |
| --- | --- | --- | --- | --- |
| `exact` | `with_review` | true | false | All critical fields match active catalog item. |
| `compatible_exact` | `with_review` | true | false | Critical fields match; optional/derived differences are acceptable. |
| `analog_candidate` | `no` | true | usually true | Validated analog layer found a candidate. |
| `needs_review` | `no` | true | sometimes true | Missing/ambiguous/unresolved fields require review. |
| `no_match` | `no` | true | sometimes true | No acceptable catalog candidate found. |
| `blocked` | `no` | true | often true | Candidate exists but hard blocker exists. |

Even `exact` is still reviewable by manager workflow. The enum does not authorize pricing, CP, invoice, PDF, or 1C actions.

## Stock Status DTO

Stock status is reported after catalog identity matching. Stock must not override critical catalog mismatch.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `stock_status` | required | string | Stock status enum value. |
| `availability_status` | required | string | High-level availability status. |
| `warehouse_results[]` | optional | array<object> | Per-warehouse stock results. |
| `expected_receipts[]` | optional | array<object> | Future receipt records. |
| `stock_snapshot_ref` | optional | string/null | Stock snapshot used. |
| `source_effective_date` | optional | string/null | Stock source effective date. |
| `manual_check_required` | required | boolean | Whether manager/manual check is required. |
| `stock_message` | required | string | Manager-facing stock explanation. |

Allowed `stock_status` values:

- `in_stock`;
- `out_of_stock`;
- `reserved_only`;
- `expected`;
- `unknown`;
- `quote_based`;
- `manual_check_required`;
- `unresolved_stock_reference`.

Rules:

- ROSMA uses latest published stock snapshot;
- non-ROSMA may be `unknown`, `manual`, or `quote_based`;
- stock cannot override critical mismatch;
- unresolved stock cannot create automatic available result.

## Related Component Result DTO

Related component result describes validation of candidate related components.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `relation_type` | required | string | Relationship type. |
| `parent_position_ref` | required | string | Parent position reference. |
| `decision` | required | string | Related component decision enum. |
| `selected_catalog_item_id` | optional | string/null | Selected related catalog/service item. |
| `selected_display_name` | optional | string/null | Display name for manager. |
| `quantity` | optional | number/null | Validated quantity if known. |
| `compatibility_status` | required | string | Parent-child compatibility result. |
| `duplicate_status` | required | string | Duplicate suppression result. |
| `manager_message` | required | string | Explanation for manager. |
| `clarification_questions[]` | required | array<string> | Questions if more data is required. |
| `validation_errors[]` | required | array<object> | Related component validation errors. |

Allowed related component decisions:

- `accepted_candidate`;
- `needs_review`;
- `blocked`;
- `duplicate_suppressed`;
- `not_requested`.

## Analog Result DTO

Analog result describes validated analog lookup output.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `decision` | required | string | Analog result decision enum. |
| `analog_catalog_item_id` | optional | string/null | Candidate analog catalog item. |
| `analog_display_name` | optional | string/null | Display name for analog candidate. |
| `source_catalog_item_id` | optional | string/null | Source/original catalog item if known. |
| `matched_fields[]` | required | array<object|string> | Fields matched by analog rule. |
| `mismatched_fields[]` | required | array<object|string> | Fields requiring attention. |
| `analog_rule_ref` | optional | string/null | Validated analog rule reference. |
| `validation_required` | required | boolean | Whether further validation is required. |
| `manager_message` | required | string | Manager-facing analog explanation. |
| `customer_confirmation_required` | required | boolean | Whether customer confirmation is required. |

Allowed `analog_result.decision` values:

- `not_requested`;
- `unavailable`;
- `candidate_found`;
- `blocked`;
- `needs_review`.

## Error DTO

Error DTOs describe invalid input, unavailable context, stale data, or blocked validation.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `error_code` | required | string | Stable error code. |
| `error_message` | required | string | Safe summary. |
| `error_severity` | required | string | `info`, `warning`, `error`, or `blocking`. |
| `field` | optional | string/null | Field related to the error. |
| `details` | optional | object | Safe structured details. |
| `source_ref` | optional | string/null | Source/audit reference. |
| `retryable` | required | boolean | Whether retry may succeed without data changes. |
| `manager_action` | required | string | Suggested manager/backend action. |

Error codes:

- `invalid_schema_version`;
- `missing_request_id`;
- `missing_required_field`;
- `invalid_product_type`;
- `invalid_product_kind`;
- `product_type_profile_not_found`;
- `not_applicable_field_used_as_required`;
- `no_active_catalog_publication`;
- `stale_catalog_publication`;
- `no_stock_snapshot`;
- `stale_stock_snapshot`;
- `unresolved_stock_reference`;
- `analog_layer_unavailable`;
- `analog_not_validated`;
- `related_component_conflict`;
- `critical_mismatch`;
- `unsafe_input_rejected`.

Error messages must not expose secrets, full prompts, credentials, raw private files, or filesystem model paths.

## Validation Rules

Request validation rules:

- request must have `schema_version`;
- request must have `request_id` and `idempotency_key`;
- request must reference Product Selector output and AgentRun;
- `product_type` must be known;
- `product_kind` must use controlled vocabulary;
- required fields depend on ProductTypeFilterProfile;
- `not_applicable` fields cannot be used as required filters;
- raw Excel/source files are not input to matcher;
- real secrets, tokens, model paths, full prompts, and private keys are rejected or redacted;
- Product Selector output remains candidate data;
- backend matcher response is decision data, not pricing/commercial approval.

## Idempotency

Idempotency rules:

- `idempotency_key` prevents duplicate matching execution;
- the same `request_id` plus same normalized input and same matching context should return the same decision or the same stored execution result;
- changing `catalog_publication_ref` creates a new matching context;
- changing `stock_snapshot_ref` creates a new availability context;
- if Product Selector output changes, the matching request should use a new idempotency key.

## Versioning

Version fields:

- `schema_version` identifies request/response DTO version;
- `matcher_version` identifies matcher rules/implementation version;
- `catalog_publication_version` identifies active catalog publication;
- `stock_snapshot_version` identifies stock snapshot used for availability;
- `product_type_profile_version` identifies filter/profile rules;
- `analog_layer_version` identifies analog rules publication;
- `related_component_rule_version` identifies related component rules publication.

Version refs should be copied into audit records so a decision can be reproduced or explained later.

## Audit References

Audit reference fields:

- `agent_run_ref`;
- `product_selector_output_ref`;
- `catalog_publication_ref`;
- `stock_snapshot_ref`;
- `analog_rule_ref`;
- `related_component_rule_ref`;
- `matcher_execution_ref`.

Do not store:

- raw prompt;
- secrets;
- real tokens;
- local filesystem model paths;
- private keys;
- production credentials.

Audit payloads should preserve enough information to explain the decision without storing sensitive data.

## Examples

All examples use demo IDs only. They do not include real prices, real stock, real catalog rows, customer data, emails, tokens, or credentials.

### Exact Match Response

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-001",
  "request_position_ref": "request_position:demo-001",
  "decision": "exact",
  "decision_reason": "All critical pressure_gauge fields match the active catalog item.",
  "decision_severity": "info",
  "selected_catalog_item_id": "catalog_item:demo-rosma-pressure-gauge-001",
  "selected_display_name": "Demo ROSMA pressure gauge 0-1 MPa G1/2 accuracy 1.0",
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "ROSMA",
  "selected_series": "TM-521",
  "selected_model": "TM-521R.00",
  "matched_fields": ["measurement_range", "range_unit", "thread", "connection_type", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": [],
  "ignored_not_applicable_fields": [],
  "rejected_candidates": [],
  "stock_status": "in_stock",
  "availability": {
    "stock_status": "in_stock",
    "availability_status": "stock_backed",
    "warehouse_results": [
      {
        "warehouse_ref": "warehouse:demo-main",
        "warehouse_name": "Demo main warehouse",
        "available_qty": 12,
        "reserved_qty": 2
      }
    ],
    "expected_receipts": [],
    "stock_snapshot_ref": "stock_snapshot:demo-rosma-latest-001",
    "source_effective_date": "2026-06-10",
    "manual_check_required": false,
    "stock_message": "Demo item has available quantity in the latest published stock snapshot."
  },
  "related_component_results": [
    {
      "relation_type": "service_position",
      "parent_position_ref": "request_position:demo-001",
      "decision": "accepted_candidate",
      "selected_catalog_item_id": "catalog_item:demo-hydrofilling-glycerin-001",
      "selected_display_name": "Demo hydrofilling with glycerin service",
      "quantity": 5,
      "compatibility_status": "compatible",
      "duplicate_status": "not_duplicate",
      "manager_message": "Hydrofilling candidate is compatible with the parent series and still requires confirmation.",
      "clarification_questions": [],
      "validation_errors": []
    }
  ],
  "analog_result": {
    "decision": "not_requested",
    "analog_catalog_item_id": null,
    "analog_display_name": null,
    "source_catalog_item_id": null,
    "matched_fields": [],
    "mismatched_fields": [],
    "analog_rule_ref": null,
    "validation_required": false,
    "manager_message": "Analog lookup was not requested.",
    "customer_confirmation_required": false
  },
  "confidence": 0.97,
  "manager_message": "Matched by critical pressure gauge fields. Review and confirm related hydrofilling service before using it downstream.",
  "clarification_questions": [],
  "source_refs": ["catalog_publication:demo-active-001", "stock_snapshot:demo-rosma-latest-001"],
  "audit_refs": ["agent_run:demo-product-selector-001", "matcher_execution:demo-001"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": "stock_snapshot:demo-rosma-latest-001",
  "next_action": "manager_review_match"
}
```

### Needs Review Response Because Thread Is Missing

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-002",
  "request_position_ref": "request_position:demo-002",
  "decision": "needs_review",
  "decision_reason": "Required field thread is missing for pressure_gauge.",
  "decision_severity": "warning",
  "selected_catalog_item_id": null,
  "selected_display_name": null,
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "ROSMA",
  "selected_series": null,
  "selected_model": null,
  "matched_fields": ["measurement_range", "range_unit", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": ["thread"],
  "ignored_not_applicable_fields": [],
  "rejected_candidates": [],
  "stock_status": "unknown",
  "availability": {
    "stock_status": "unknown",
    "availability_status": "unknown",
    "warehouse_results": [],
    "expected_receipts": [],
    "stock_snapshot_ref": null,
    "source_effective_date": null,
    "manual_check_required": true,
    "stock_message": "Stock lookup was not performed because catalog identity was not selected."
  },
  "related_component_results": [],
  "analog_result": {
    "decision": "not_requested",
    "analog_catalog_item_id": null,
    "analog_display_name": null,
    "source_catalog_item_id": null,
    "matched_fields": [],
    "mismatched_fields": [],
    "analog_rule_ref": null,
    "validation_required": false,
    "manager_message": "Analog lookup was not requested.",
    "customer_confirmation_required": false
  },
  "confidence": 0.41,
  "manager_message": "Cannot select a catalog item until connection thread is clarified.",
  "clarification_questions": ["Clarify pressure gauge connection/thread."],
  "source_refs": ["catalog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-002", "matcher_execution:demo-002"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": null,
  "next_action": "ask_customer_clarification"
}
```

### Blocked Response Because Range Mismatched

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-003",
  "request_position_ref": "request_position:demo-003",
  "decision": "blocked",
  "decision_reason": "Candidate has a critical measurement range mismatch.",
  "decision_severity": "blocking",
  "selected_catalog_item_id": null,
  "selected_display_name": null,
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "ROSMA",
  "selected_series": null,
  "selected_model": null,
  "matched_fields": ["thread", "accuracy_class"],
  "mismatched_fields": [
    {
      "field": "measurement_range",
      "requested": "0-1 MPa",
      "candidate": "0-1.6 MPa",
      "critical": true
    }
  ],
  "missing_fields": [],
  "ignored_not_applicable_fields": [],
  "rejected_candidates": [
    {
      "catalog_item_id": "catalog_item:demo-rejected-range-001",
      "reason": "critical_mismatch",
      "field": "measurement_range"
    }
  ],
  "stock_status": "unknown",
  "availability": {
    "stock_status": "unknown",
    "availability_status": "unknown",
    "warehouse_results": [],
    "expected_receipts": [],
    "stock_snapshot_ref": null,
    "source_effective_date": null,
    "manual_check_required": true,
    "stock_message": "Stock lookup is blocked by catalog mismatch."
  },
  "related_component_results": [],
  "analog_result": {
    "decision": "not_requested",
    "analog_catalog_item_id": null,
    "analog_display_name": null,
    "source_catalog_item_id": null,
    "matched_fields": [],
    "mismatched_fields": [],
    "analog_rule_ref": null,
    "validation_required": false,
    "manager_message": "Analog lookup was not requested.",
    "customer_confirmation_required": false
  },
  "confidence": 0.2,
  "manager_message": "Do not use the rejected candidate automatically because measurement range differs from required value.",
  "clarification_questions": ["Confirm whether a different pressure range is acceptable."],
  "source_refs": ["catalog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-003", "matcher_execution:demo-003"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": null,
  "next_action": "manager_review_blocked_candidate"
}
```

### Expected Stock Response For ROSMA Item

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-004",
  "request_position_ref": "request_position:demo-004",
  "decision": "exact",
  "decision_reason": "Catalog item matches, but latest ROSMA stock snapshot shows future receipt instead of current free stock.",
  "decision_severity": "warning",
  "selected_catalog_item_id": "catalog_item:demo-rosma-expected-001",
  "selected_display_name": "Demo ROSMA stock-backed item",
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "ROSMA",
  "selected_series": "TM-521",
  "selected_model": "TM-521R.00",
  "matched_fields": ["measurement_range", "range_unit", "thread", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": [],
  "ignored_not_applicable_fields": [],
  "rejected_candidates": [],
  "stock_status": "expected",
  "availability": {
    "stock_status": "expected",
    "availability_status": "stock_backed_expected",
    "warehouse_results": [
      {
        "warehouse_ref": "warehouse:demo-main",
        "warehouse_name": "Demo main warehouse",
        "available_qty": 0,
        "reserved_qty": 0
      }
    ],
    "expected_receipts": [
      {
        "date": "2026-07-15",
        "qty": 20,
        "source_column": "demo_expected_receipt"
      }
    ],
    "stock_snapshot_ref": "stock_snapshot:demo-rosma-latest-001",
    "source_effective_date": "2026-06-10",
    "manual_check_required": false,
    "stock_message": "Current free stock is zero; future receipt is available in the latest published snapshot."
  },
  "related_component_results": [],
  "analog_result": {
    "decision": "not_requested",
    "analog_catalog_item_id": null,
    "analog_display_name": null,
    "source_catalog_item_id": null,
    "matched_fields": [],
    "mismatched_fields": [],
    "analog_rule_ref": null,
    "validation_required": false,
    "manager_message": "Analog lookup was not requested.",
    "customer_confirmation_required": false
  },
  "confidence": 0.94,
  "manager_message": "Catalog item matches. Availability is expected from future receipt rather than current stock.",
  "clarification_questions": [],
  "source_refs": ["catalog_publication:demo-active-001", "stock_snapshot:demo-rosma-latest-001"],
  "audit_refs": ["agent_run:demo-product-selector-004", "matcher_execution:demo-004"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": "stock_snapshot:demo-rosma-latest-001",
  "next_action": "manager_review_stock_expected"
}
```

### Analog Candidate Response

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-005",
  "request_position_ref": "request_position:demo-005",
  "decision": "analog_candidate",
  "decision_reason": "Validated analog layer returned a candidate that requires manager and customer confirmation.",
  "decision_severity": "warning",
  "selected_catalog_item_id": "catalog_item:demo-analog-001",
  "selected_display_name": "Demo validated analog item",
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "DemoManufacturer",
  "selected_series": "DemoSeries",
  "selected_model": "DemoModel",
  "matched_fields": ["measurement_range", "range_unit", "thread", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": [],
  "ignored_not_applicable_fields": [],
  "rejected_candidates": [],
  "stock_status": "manual_check_required",
  "availability": {
    "stock_status": "manual_check_required",
    "availability_status": "manual",
    "warehouse_results": [],
    "expected_receipts": [],
    "stock_snapshot_ref": null,
    "source_effective_date": null,
    "manual_check_required": true,
    "stock_message": "Analog candidate requires manager confirmation before stock interpretation."
  },
  "related_component_results": [],
  "analog_result": {
    "decision": "candidate_found",
    "analog_catalog_item_id": "catalog_item:demo-analog-001",
    "analog_display_name": "Demo validated analog item",
    "source_catalog_item_id": null,
    "matched_fields": ["measurement_range", "range_unit", "thread", "accuracy_class"],
    "mismatched_fields": [],
    "analog_rule_ref": "analog_rule:demo-published-001",
    "validation_required": true,
    "manager_message": "Analog rule exists, but manager must confirm acceptability before downstream use.",
    "customer_confirmation_required": true
  },
  "confidence": 0.76,
  "manager_message": "Validated analog candidate found. Confirm analog acceptance before using it in the request workflow.",
  "clarification_questions": ["Confirm whether the proposed analog is acceptable."],
  "source_refs": ["catalog_publication:demo-active-001", "analog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-005", "matcher_execution:demo-005"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": null,
  "next_action": "manager_confirm_analog"
}
```

### Error Response For not_applicable_field_used_as_required

```json
{
  "schema_version": "catalog-matcher-api-v1",
  "matcher_version": "catalog-matcher-doc-v1",
  "request_id": "matcher_request:demo-006",
  "request_position_ref": "request_position:demo-006",
  "decision": "needs_review",
  "decision_reason": "Request used a not-applicable field as a required filter for pressure_gauge.",
  "decision_severity": "warning",
  "selected_catalog_item_id": null,
  "selected_display_name": null,
  "selected_product_type": "pressure_gauge",
  "selected_manufacturer": "ROSMA",
  "selected_series": null,
  "selected_model": null,
  "matched_fields": [],
  "mismatched_fields": [],
  "missing_fields": [],
  "ignored_not_applicable_fields": [
    {
      "field": "immersion_length",
      "reason": "ProductTypeFilterProfile marks immersion_length as not_applicable for pressure_gauge."
    }
  ],
  "rejected_candidates": [],
  "stock_status": "unknown",
  "availability": {
    "stock_status": "unknown",
    "availability_status": "unknown",
    "warehouse_results": [],
    "expected_receipts": [],
    "stock_snapshot_ref": null,
    "source_effective_date": null,
    "manual_check_required": true,
    "stock_message": "Stock lookup was not performed because request validation requires review."
  },
  "related_component_results": [],
  "analog_result": {
    "decision": "not_requested",
    "analog_catalog_item_id": null,
    "analog_display_name": null,
    "source_catalog_item_id": null,
    "matched_fields": [],
    "mismatched_fields": [],
    "analog_rule_ref": null,
    "validation_required": false,
    "manager_message": "Analog lookup was not requested.",
    "customer_confirmation_required": false
  },
  "confidence": 0.0,
  "manager_message": "The matcher ignored immersion_length because it is not applicable to pressure gauges. Review Product Selector output or request mapping.",
  "clarification_questions": [],
  "source_refs": ["catalog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-006", "matcher_execution:demo-006"],
  "catalog_publication_ref": "catalog_publication:demo-active-001",
  "stock_snapshot_ref": null,
  "next_action": "review_validation_warning",
  "errors": [
    {
      "error_code": "not_applicable_field_used_as_required",
      "error_message": "A not-applicable field was used as a required matcher filter.",
      "error_severity": "warning",
      "field": "immersion_length",
      "details": {
        "product_type": "pressure_gauge",
        "profile_ref": "product_type_profile:demo-pressure-gauge"
      },
      "source_ref": "agent_output:demo-product-selector-006",
      "retryable": false,
      "manager_action": "Review mapping and remove the not-applicable requirement."
    }
  ]
}
```

## Relationship To Existing Docs

Related documentation:

- [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md) defines LLM-agent output envelopes and backend-service output boundaries.
- [Catalog Data Model](CATALOG_MODEL.md) defines constructor-style catalog model and ProductTypeFilterProfile.
- [Catalog Source Mapping](CATALOG_SOURCE_MAPPING.md) defines how source rows are normalized into catalog candidates.
- [ROSMA Catalog Import Plan](ROSMA_CATALOG_IMPORT_PLAN.md) defines catalog and daily stock import flow.
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md) defines matcher responsibilities, query strategy, decision taxonomy, and boundaries.
- [Product Selector Rulebook](PRODUCT_SELECTOR_RULEBOOK.md) defines Product Selector behavior and candidate-data constraints.
- [Product Selector Related Component Rules](PRODUCT_SELECTOR_RELATED_COMPONENTS.md) defines related component suggestion rules.

This API contract should stay aligned with those documents when implementation starts.

## Deferred Implementation

Deferred work:

- FastAPI implementation;
- routes, controllers, and services;
- database schema;
- SQL, ORM, and migrations;
- indexes and search engine;
- parser/import runner;
- UI;
- tests;
- pricing;
- CP/invoice/PDF generation;
- 1C exchange;
- scheduler;
- real analog reference data;
- exact runtime validation library;
- exact persistence model for matcher executions.

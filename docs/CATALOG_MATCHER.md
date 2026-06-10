# Backend Catalog Matcher Design

This document defines the documentation-only design for Backend Catalog Matcher in ArtCRM.

It does not add backend code, frontend code, database schema, SQL, ORM, migrations, parser/import runner, API endpoints, UI, pricing logic, CP/invoice/PDF/1C flow, dependencies, containers, Ollama calls, model or Modelfile changes, `.env.example` changes, Excel files, real catalog rows, real stock rows, real prices, customer data, production emails, credentials, tokens, secrets, private keys, or filesystem model paths.

## Purpose

Backend Catalog Matcher is a backend-only decision service for catalog matching after Product Selector has produced candidate structured intent and backend validation has checked the LLM output envelope.

Backend Catalog Matcher is:

- the source of catalog matching decisions after Product Selector;
- a deterministic backend service boundary;
- a consumer of active catalog publications and latest published stock snapshots;
- a validator of critical product fields, related component suggestions, and analog candidates;
- a producer of machine-readable decisions and manager-facing explanations.

Backend Catalog Matcher is not:

- an LLM;
- an Excel parser;
- an import runner;
- a UI;
- a pricing service;
- a CP, invoice, PDF, or 1C service;
- a replacement for catalog import validation;
- a direct consumer of raw Excel as a source of truth.

The matcher exists so Product Selector candidate data can be checked against active, reviewed, versioned catalog data before a manager uses it in a request workflow.

## Matcher Responsibilities

Backend Catalog Matcher should:

- accept backend-validated Product Selector structured intent;
- determine manufacturer scope;
- determine `product_type`;
- load `ProductTypeFilterProfile` by manufacturer scope and product type;
- check required, optional, derived, and `not_applicable` fields;
- find candidate `CatalogItem` / SKU records in the active catalog publication;
- check critical fields for the specific product type;
- validate related component suggestions;
- validate analog candidates through the analog layer when applicable;
- read the latest published ROSMA stock snapshot after catalog identity is matched;
- return `unknown`, `manual`, or `quote_based` availability for non-ROSMA catalog-only manufacturers when no stock feed exists;
- return a machine-readable decision and manager-facing explanation;
- include source and audit references so the decision can be reviewed later.

The matcher should treat all Product Selector fields as candidate data. Product Selector confidence may help triage review priority, but it is not business approval and must not override catalog validation.

## Non-Responsibilities

Backend Catalog Matcher must not:

- parse Excel;
- import catalog data;
- import stock data;
- call Ollama;
- change or repair Product Selector prompt/model behavior;
- generate prices;
- calculate CP totals;
- create invoices;
- generate PDFs;
- perform 1C exchange;
- create real `RequestPosition` records without a separate backend workflow;
- trust raw Excel directly;
- accept LLM output as source of truth;
- approve analogs that are not present in a validated analog layer;
- add related components to CP/invoice/request positions as confirmed items without manager/backend workflow confirmation.

## Inputs

The matcher receives a backend-validated matching request. The input should reference the original request position and agent run, but it should not embed secrets, credentials, full prompts, or private source files.

Conceptual input fields:

- `request_position_ref`;
- `agent_run_ref`;
- `product_selector_output_ref`;
- `source_text`;
- `normalized_text`;
- `manufacturer_scope`;
- `product_type`;
- `product_kind`;
- `structured_intent`;
- `must_have[]`;
- `forbidden_mismatch[]`;
- `missing_fields[]`;
- `related_component_suggestions[]`;
- `analog_request`;
- `validation_hints`.

Example input:

```json
{
  "request_position_ref": "request_position:demo-001",
  "agent_run_ref": "agent_run:demo-product-selector-001",
  "product_selector_output_ref": "agent_output:demo-product-selector-001",
  "source_text": "Манометр ТМ-521Р.00 0-1 МПа G1/2 кл.1,0, 5 шт., с глицерином",
  "normalized_text": "pressure gauge TM-521R.00 0-1 MPa G1/2 accuracy 1.0 qty 5 hydrofilling glycerin",
  "manufacturer_scope": "ROSMA",
  "product_type": "pressure_gauge",
  "product_kind": "main_product",
  "structured_intent": {
    "model_candidate": "TM-521R.00",
    "measurement_range": "0-1",
    "range_unit": "MPa",
    "thread": "G1/2",
    "connection_type": "radial",
    "accuracy_class": "1.0",
    "quantity": 5,
    "case_diameter": 100,
    "hydrofilling_requested": true,
    "hydrofilling_fluid_type": "glycerin"
  },
  "must_have": [
    { "field": "measurement_range", "value": "0-1" },
    { "field": "range_unit", "value": "MPa" },
    { "field": "thread", "value": "G1/2" },
    { "field": "accuracy_class", "value": "1.0" }
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
      "suggested_model_candidate": "Гидрозаполнение глицерином для манометра диам.100 — 5 шт.",
      "parent_position_ref": "request_position:demo-001",
      "quantity_policy": "same_as_parent",
      "quantity_candidate": 5,
      "requires_confirmation": true,
      "backend_validation_required": true,
      "manufacturer_scope": "ROSMA"
    }
  ],
  "analog_request": {
    "requested": false
  },
  "validation_hints": {
    "llm_output_is_candidate_data": true,
    "backend_validation_completed": true
  }
}
```

## ProductTypeFilterProfile Enforcement

The matcher must load `ProductTypeFilterProfile` by `product_type` and `manufacturer_scope` before matching.

Rules:

- missing required fields return `needs_review`;
- `not_applicable` fields used as required filters produce a validation warning or rejected filter;
- optional fields improve ranking but must not block a match by themselves;
- derived fields may be calculated from normalized catalog data or source hierarchy;
- Product Selector fields are never trusted without checking against the profile;
- profile enforcement happens before search string similarity is allowed to influence ranking.

Examples:

- `pressure_gauge` must not require `immersion_length`;
- `bimetal_thermometer` requires `temperature_range` and `immersion_length`;
- `thermowell` requires `compatible_parent_series`, `L`, `d`, and `thread` or `thread_pair`;
- `pressure_transducer` requires `signal_output`;
- `thermomanometer` requires `pressure_range` and `temperature_range`;
- `solenoid_valve` requires `valve_function` and `voltage_or_coil`;
- `service_position` has own `thread` as `not_applicable` by default unless a subtype-specific profile explicitly overrides it.

## Catalog Query Strategy

The matcher should search in controlled stages:

1. Normalize intent fields.
2. Select active catalog publication.
3. Filter by manufacturer scope.
4. Filter by `product_type`.
5. Apply exact normalized field lookup.
6. Apply parameter lookup.
7. Apply search variants only as secondary candidate discovery.
8. Apply source hierarchy hints only as explainability or secondary hints.
9. Score and rank candidates.
10. Apply critical mismatch rules.
11. Produce decision.

Rules:

- active catalog publication is the only catalog source for matching;
- raw Excel is not read by matcher;
- search string similarity cannot override critical field mismatch;
- source hierarchy can explain why a candidate was found, but it must not replace field validation;
- exact code/model matches can improve ranking, but critical fields still must match;
- candidates rejected by hard blockers must be recorded in `rejected_candidates[]`.

## Critical Field Checks

Critical fields depend on `product_type`.

### pressure_gauge / vacuum_gauge / manovacuum_gauge

Critical fields:

- `measurement_range`;
- `range_unit`;
- `thread`;
- `connection_type`;
- `accuracy_class`;
- `material` if present in `must_have`;
- `execution` if present in `must_have`;
- hydrofilling support if a hydrofilling service is requested.

### bimetal_thermometer

Critical fields:

- `temperature_range`;
- `thread`;
- `immersion_length`;
- `stem_diameter` if required by compatible thermowell;
- `material` if present in `must_have`.

### thermowell

Critical fields:

- `compatible_parent_type`;
- `compatible_parent_series`;
- `immersion_length`;
- `stem_diameter`;
- `thread` or `thread_pair`;
- `material` if present in `must_have`.

### pressure_transducer

Critical fields:

- `measurement_range`;
- `range_unit`;
- `thread`;
- `signal_output`;
- `accuracy_class`;
- `material` or `protection_rating` if present in `must_have`.

### thermomanometer

Critical fields:

- `pressure_range`;
- `pressure_range_unit`;
- `temperature_range`;
- `temperature_unit`;
- `thread`;
- `connection_type`;
- pressure accuracy candidate if available.

A thermomanometer must not be treated as a normal pressure gauge because it has both pressure and temperature circuits.

### solenoid_valve

Critical fields:

- `valve_function`;
- `voltage_or_coil`;
- `port`, `DN`, or `thread`;
- `medium`;
- `pressure_limit` if required by request or catalog profile.

A solenoid valve must not be hidden inside a generic valve profile when coil/voltage fields are needed.

### service_position

Critical fields:

- `service_type`;
- `parent_position_ref` or `parent_product_type`;
- `quantity_policy`;
- `fluid_type` if the service is hydrofilling;
- parent compatibility;
- own `thread` is `not_applicable` by default.

## Decision Taxonomy

| Decision | Meaning | When Returned | Manager Use | Customer Clarification |
| --- | --- | --- | --- | --- |
| `exact` | All critical fields match an active catalog item. | A single strong catalog candidate passes critical checks. | Can be used as a proposed match, still reviewable by manager workflow. | Usually not needed. |
| `compatible_exact` | Critical fields match, while optional or derived fields differ but are acceptable. | Candidate is compatible after profile-aware validation. | Can be used after manager sees explanation. | Usually not needed unless optional fields matter commercially. |
| `analog_candidate` | Validated analog layer produced a candidate. | Requested item is not directly matched or analog request is explicit and analog rule exists. | Requires manager/backend confirmation. | May be needed to confirm analog acceptance. |
| `needs_review` | More human review is required. | Required field is missing, candidates are ambiguous, confidence is low, related component is unresolved, or stock is unresolved. | Manager must review before use. | Often needed. |
| `no_match` | No catalog candidate was found after allowed search stages. | Search exhausted without acceptable candidates. | Cannot use as matched item. | May ask customer for more details or handle manually. |
| `blocked` | A candidate exists but a hard critical mismatch exists. | Wrong range, unit, thread, signal, unsupported service, or other blocker is found. | Must not use automatically. | Usually needed unless manager chooses a different product. |

Decision rules:

- `exact`: all critical fields match active catalog item.
- `compatible_exact`: critical fields match, optional/derived fields differ but are acceptable.
- `analog_candidate`: analog layer produced candidate, but manager/backend validation is still required.
- `needs_review`: missing required field, ambiguous candidates, low confidence, unresolved related component, or unresolved stock.
- `no_match`: no catalog candidate found after allowed search stages.
- `blocked`: candidate found but critical mismatch exists.

## Blocking Rules

Hard blockers include:

- wrong range;
- wrong unit;
- wrong thread;
- wrong `connection_type` when critical;
- wrong `accuracy_class`;
- wrong `material` when present in `must_have`;
- wrong `execution` when present in `must_have`;
- missing `signal_output` for `pressure_transducer`;
- thermomanometer missing pressure or temperature circuit;
- thermowell wrong `L`, `d`, `thread`, or `thread_pair`;
- hydrofilling requested for unsupported series;
- related component incompatible with parent;
- Product Selector candidate uses a `not_applicable` field as a required filter;
- analog requested but analog policy forbids it or no validated analog rule exists.

Blocking rules are stronger than text similarity, optional field matches, Product Selector confidence, and source hierarchy hints.

## Missing Required Fields

The matcher must not invent missing values.

Rules:

- missing required field returns `needs_review`;
- output must include `clarification_questions[]`;
- output must include `manager_message`;
- missing values may be listed in `missing_fields[]` and `validation_hints`;
- the matcher may suggest which field must be clarified, but it must not fill it from guesswork.

Examples:

- no thread -> ask customer or manager to clarify connection/thread;
- thermometer without `L` -> ask for immersion length;
- hydrofilling without fluid type -> ask whether the fluid is glycerin or silicone;
- pressure transducer without `signal_output` -> ask for output signal.

## Stock / Availability Boundary

Stock lookup happens after catalog identity matching.

Rules:

- matcher first finds a catalog candidate;
- stock lookup is after catalog identity matching;
- ROSMA uses the latest published stock snapshot;
- non-ROSMA may return `availability_status=unknown`, `manual`, or `quote_based`;
- unresolved stock rows must not produce an automatic available result;
- stock status must include source/version reference;
- stock data cannot override critical catalog mismatch;
- stock data is never Product Selector output.

Stock statuses:

- `in_stock`;
- `out_of_stock`;
- `reserved_only`;
- `expected`;
- `unknown`;
- `quote_based`;
- `manual_check_required`;
- `unresolved_stock_reference`.

Availability fields should identify whether the answer is stock-backed, manually entered, quote-based, or unknown.

## Related Component Validation

Product Selector related component suggestions are candidates only.

The matcher should:

- validate parent-child compatibility;
- check duplicate suppression;
- check `quantity_policy`;
- check required parent fields;
- return `needs_review` for missing parent fields;
- block incompatible related components;
- keep related component decisions separate from the main catalog item decision.

Examples:

- hydrofilling for supported ROSMA series 20/21/521-style families can be validated as a candidate service-position;
- hydrofilling for unsupported series returns `blocked` or `needs_review` depending on policy and available catalog metadata;
- thermowell requires parent thermometer series and immersion length `L`;
- bushing requires compatible thread;
- if a related component is already present in the request, duplicate suggestion should be suppressed rather than added again.

## Analog Lookup Boundary

The matcher may conceptually use the analog layer, but analogs must come from validated and published analog data.

Rules:

- no LLM-invented analogs;
- analog layer must be validated and published;
- ART-35 remains a separate backlog item for analog reference data;
- if no validated analog data exists, return `no_match` or `needs_review`, not an invented analog;
- `analog_candidate` must explain which fields match and which require confirmation;
- analog candidates must not bypass hard blockers unless analog policy explicitly allows the substitution and all required analog compatibility fields pass validation.

## Output DTO

The matcher returns a machine-readable result and a manager-facing explanation.

Common output fields:

- `matcher_version`;
- `request_position_ref`;
- `decision`;
- `decision_reason`;
- `product_type`;
- `selected_catalog_item_id`;
- `selected_display_name`;
- `matched_fields[]`;
- `mismatched_fields[]`;
- `missing_fields[]`;
- `rejected_candidates[]`;
- `stock_status`;
- `availability`;
- `related_component_results[]`;
- `analog_result`;
- `confidence`;
- `manager_message`;
- `clarification_questions[]`;
- `source_refs[]`;
- `audit_refs[]`;
- `next_action`.

### Exact Match Output

```json
{
  "matcher_version": "catalog-matcher-doc-v1",
  "request_position_ref": "request_position:demo-001",
  "decision": "exact",
  "decision_reason": "All critical pressure_gauge fields match the active ROSMA catalog item.",
  "product_type": "pressure_gauge",
  "selected_catalog_item_id": "catalog_item:demo-rosma-tm521-0-1mpa-g12-10",
  "selected_display_name": "ROSMA TM-521R.00 0-1 MPa G1/2 accuracy 1.0",
  "matched_fields": [
    "manufacturer_scope",
    "product_type",
    "measurement_range",
    "range_unit",
    "thread",
    "connection_type",
    "accuracy_class"
  ],
  "mismatched_fields": [],
  "missing_fields": [],
  "rejected_candidates": [],
  "stock_status": "in_stock",
  "availability": {
    "status": "in_stock",
    "available_qty": 12,
    "reserved_qty": 2,
    "source_type": "latest_published_stock_snapshot"
  },
  "related_component_results": [
    {
      "suggested_type": "hydrofilling",
      "decision": "compatible_exact",
      "requires_confirmation": true,
      "backend_validation_required": true,
      "reason": "Parent series supports hydrofilling and fluid type is provided."
    }
  ],
  "analog_result": {
    "requested": false,
    "decision": "not_applicable"
  },
  "confidence": 0.97,
  "manager_message": "Matched ROSMA pressure gauge by range, unit, thread, connection type, and accuracy class. Hydrofilling is a candidate service-position and still requires confirmation.",
  "clarification_questions": [],
  "source_refs": [
    "catalog_publication:demo-active-001",
    "stock_snapshot:demo-rosma-latest-001"
  ],
  "audit_refs": [
    "agent_run:demo-product-selector-001",
    "matcher_run:demo-001"
  ],
  "next_action": "manager_review_match"
}
```

### Needs Review Output For Missing Thread

```json
{
  "matcher_version": "catalog-matcher-doc-v1",
  "request_position_ref": "request_position:demo-002",
  "decision": "needs_review",
  "decision_reason": "Required field thread is missing for pressure_gauge.",
  "product_type": "pressure_gauge",
  "selected_catalog_item_id": null,
  "selected_display_name": null,
  "matched_fields": ["manufacturer_scope", "product_type", "measurement_range", "range_unit", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": ["thread"],
  "rejected_candidates": [],
  "stock_status": "unknown",
  "availability": {
    "status": "unknown",
    "reason": "Catalog identity was not selected, so stock lookup was not performed."
  },
  "related_component_results": [],
  "analog_result": {
    "requested": false,
    "decision": "not_applicable"
  },
  "confidence": 0.42,
  "manager_message": "Cannot select a pressure gauge without connection/thread. Ask the customer to clarify the thread.",
  "clarification_questions": [
    "Уточнить присоединение/резьбу манометра?"
  ],
  "source_refs": ["catalog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-002", "matcher_run:demo-002"],
  "next_action": "ask_customer_clarification"
}
```

### Blocked Output For Wrong Range

```json
{
  "matcher_version": "catalog-matcher-doc-v1",
  "request_position_ref": "request_position:demo-003",
  "decision": "blocked",
  "decision_reason": "Candidate range does not match the required measurement range.",
  "product_type": "pressure_gauge",
  "selected_catalog_item_id": null,
  "selected_display_name": null,
  "matched_fields": ["manufacturer_scope", "product_type", "thread", "accuracy_class"],
  "mismatched_fields": [
    {
      "field": "measurement_range",
      "requested": "0-1 MPa",
      "candidate": "0-1.6 MPa",
      "critical": true
    }
  ],
  "missing_fields": [],
  "rejected_candidates": [
    {
      "catalog_item_id": "catalog_item:demo-rejected-range",
      "reason": "wrong_range",
      "critical": true
    }
  ],
  "stock_status": "unknown",
  "availability": {
    "status": "unknown",
    "reason": "Stock lookup is not allowed for blocked catalog mismatch."
  },
  "related_component_results": [],
  "analog_result": {
    "requested": false,
    "decision": "not_applicable"
  },
  "confidence": 0.18,
  "manager_message": "A similar item exists, but pressure range is different. Do not use it as a match without manager decision and customer confirmation.",
  "clarification_questions": [
    "Подтвердить, допустим ли диапазон 0-1.6 MPa вместо 0-1 MPa?"
  ],
  "source_refs": ["catalog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-003", "matcher_run:demo-003"],
  "next_action": "manager_review_blocked_candidate"
}
```

### ROSMA Expected Stock Output

```json
{
  "matcher_version": "catalog-matcher-doc-v1",
  "request_position_ref": "request_position:demo-004",
  "decision": "exact",
  "decision_reason": "Catalog item matches, but latest ROSMA stock snapshot shows no current free stock and a future receipt.",
  "product_type": "pressure_gauge",
  "selected_catalog_item_id": "catalog_item:demo-rosma-stock-expected",
  "selected_display_name": "ROSMA pressure gauge demo item",
  "matched_fields": ["manufacturer_scope", "product_type", "measurement_range", "range_unit", "thread", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": [],
  "rejected_candidates": [],
  "stock_status": "expected",
  "availability": {
    "status": "expected",
    "available_qty": 0,
    "reserved_qty": 0,
    "expected_receipts": [
      {
        "date": "2026-07-15",
        "qty": 20,
        "source_column": "demo_expected_receipt"
      }
    ],
    "stock_snapshot_version": "stock_snapshot:demo-rosma-latest-001",
    "source_effective_date": "2026-06-10"
  },
  "related_component_results": [],
  "analog_result": {
    "requested": false,
    "decision": "not_applicable"
  },
  "confidence": 0.94,
  "manager_message": "Catalog item matches. Current stock is zero, but a future receipt is present in the latest ROSMA stock snapshot.",
  "clarification_questions": [],
  "source_refs": ["catalog_publication:demo-active-001", "stock_snapshot:demo-rosma-latest-001"],
  "audit_refs": ["agent_run:demo-product-selector-004", "matcher_run:demo-004"],
  "next_action": "manager_review_stock_expected"
}
```

### Analog Candidate Output

```json
{
  "matcher_version": "catalog-matcher-doc-v1",
  "request_position_ref": "request_position:demo-005",
  "decision": "analog_candidate",
  "decision_reason": "No direct catalog match was selected, but the validated analog layer returned a compatible candidate requiring confirmation.",
  "product_type": "pressure_gauge",
  "selected_catalog_item_id": "catalog_item:demo-analog-candidate",
  "selected_display_name": "Validated analog pressure gauge demo item",
  "matched_fields": ["measurement_range", "range_unit", "thread", "accuracy_class"],
  "mismatched_fields": [],
  "missing_fields": [],
  "rejected_candidates": [],
  "stock_status": "manual_check_required",
  "availability": {
    "status": "manual_check_required",
    "reason": "Analog candidate requires manager confirmation before stock interpretation."
  },
  "related_component_results": [],
  "analog_result": {
    "requested": true,
    "decision": "analog_candidate",
    "analog_rule_ref": "analog_rule:demo-published-001",
    "requires_confirmation": true,
    "matched_fields": ["measurement_range", "range_unit", "thread", "accuracy_class"],
    "fields_requiring_confirmation": ["manufacturer", "execution"]
  },
  "confidence": 0.76,
  "manager_message": "Validated analog candidate found. Confirm analog acceptance and execution before using it in the request workflow.",
  "clarification_questions": [
    "Подтвердить, допустим ли предложенный аналог?"
  ],
  "source_refs": ["catalog_publication:demo-active-001", "analog_publication:demo-active-001"],
  "audit_refs": ["agent_run:demo-product-selector-005", "matcher_run:demo-005"],
  "next_action": "manager_confirm_analog"
}
```

## Manager-Facing Explanation

The matcher must explain decisions in language a manager can act on.

Explanation should include:

- why a candidate was selected;
- why a candidate was rejected;
- what field is missing;
- what question to ask the customer;
- whether stock is known;
- whether the item is ROSMA stock-backed or non-ROSMA catalog-only;
- whether an analog or related component needs confirmation;
- which catalog and stock versions were used.

Manager-facing text must not expose secrets, credentials, full prompts, private source files, or implementation-only debug payloads.

## Relationship To Product Selector

Product Selector provides candidate structured intent. The matcher validates and decides.

Rules:

- matcher can reject Product Selector fields;
- matcher can ignore `not_applicable` fields;
- matcher can ask for clarification;
- Product Selector confidence is not business approval;
- Product Selector related component suggestions remain candidates until matcher/backend validation and manager confirmation;
- Product Selector must not determine stock, price, CP, invoice, PDF, or 1C outcomes.

## Relationship To Catalog Import

Backend Catalog Matcher uses only published import results.

Rules:

- matcher uses active catalog publication only;
- matcher uses latest stock snapshot only;
- matcher does not trust raw Excel;
- matcher should reference `catalog_publication_version` and `stock_snapshot_version` in output;
- stale, rejected, archived, or unresolved import records must not be treated as active source of truth;
- unresolved stock rows must not produce automatic stock availability.

## Relationship To Future Implementation

Deferred implementation decisions:

- database schema;
- indexes;
- search engine;
- scoring thresholds;
- API endpoints;
- UI;
- parser implementation;
- import runner;
- pricing;
- 1C exchange;
- CP/invoice/PDF generation;
- exact audit storage format;
- exact manager workflow for approving matches, analogs, and related components.

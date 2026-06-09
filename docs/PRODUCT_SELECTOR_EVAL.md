# Product Selector Agent Quality Evaluation Plan

This document defines the documentation-only quality evaluation plan for the Product Selector Agent / CRM Position Intent Agent before backend integration. It does not modify the model, call Ollama, add backend code, add frontend code, create automated fixtures, add dependencies, or introduce real customer data.

## Purpose

The Product Selector Agent already exists as local Ollama model logic, but the current result is not accepted by the product owner. Before backend integration, ArtCRM needs a repeatable quality plan that defines:

- which synthetic product lines to test;
- which JSON fields the model must extract;
- which industrial matching fields are critical;
- which mistakes are blocking;
- when `needs_review` is required;
- which pass/fail criteria are used;
- how this plan can later become automated evaluation fixtures.

The goal is not to approve the model automatically. The goal is to make quality review explicit before the agent can support RequestPosition parsing and Backend Catalog Matcher input.

## Model Under Test

- Model name: `artmatica-product-selector-gemma:latest`.
- Runtime: local Ollama, when future evaluation execution is implemented.
- `model_name` must be recorded as `artmatica-product-selector-gemma:latest` in future AgentRun quality records.
- This document does not use or define a filesystem model path.
- This task must not call Ollama or modify the installed model.

Related existing model context:

- Mail Reader Agent model: `artmatica-mail-reader-gemma:latest`.
- Mail Reader Agent output may become context for Product Selector evaluation in future pipeline tests, but this document evaluates the Product Selector contract only.

## Expected Output Contract

The Product Selector Agent output is LLM candidate data. It must use the Shared LLM Agent Output Envelope from [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md), with Product Selector payload fields.

Expected envelope fields:

- `schema_version`
- `agent_name`
- `agent_role`
- `output_type`
- `status`
- `confidence`
- `source_refs`
- `payload`
- `validation_hints`
- `next_action`

Expected payload fields:

- `source_text`
- `normalized_text`
- `intent.product_type`
- `intent.manufacturer`
- `intent.series`
- `intent.model`
- `intent.range`
- `intent.connection`
- `intent.accuracy_class`
- `intent.material`
- `intent.execution`
- `intent.options[]`
- `intent.quantity`
- `intent.unit`
- `search.main_query`
- `search.search_variants[]`
- `must_have[]`
- `forbidden_mismatch[]`
- `analog_request`
- `needs_clarification`
- `clarification_questions[]`
- `manufacturer_scope`
- `rosma_model_candidate`
- `related_component_suggestions[]`

Required boundaries:

- Output remains candidate data.
- Backend validation remains mandatory.
- Product Selector must not approve `catalog_item_id`.
- Product Selector must not calculate prices, VAT, totals, delivery terms, or document values.
- Product Selector must not fabricate missing critical parameters.
- Product Selector must not claim a final catalog match.
- Product Selector must not add related components as confirmed positions.

## Critical Fields for Industrial Product Matching

Critical fields are fields that can change whether an item is compatible or safe to offer. Missing or contradictory values should usually produce `needs_clarification: true` and downstream `needs_review`.

Critical fields:

- `intent.product_type` - main product class, such as pressure gauge, vacuum gauge, pressure transducer, or accessory.
- `intent.range` - measurement range and sign, such as `0-10 bar`, `-1..0 bar`, or `0-1 MPa`.
- `intent.unit` - requested quantity unit, such as `pcs`, `set`, or another normalized unit.
- `intent.quantity` - numeric requested quantity.
- `intent.connection` - thread, process connection, or mounting connection.
- `intent.accuracy_class` - accuracy class when required by product family.
- `intent.material` - wetted or case material where relevant.
- `intent.execution` - execution variant, such as axial/radial, explosion-proof, vibration-resistant, or sealed.
- `intent.options[]` - options that may materially affect catalog choice.
- `analog_request.allowed` - whether customer explicitly allows analogs.
- `must_have[]` - constraints that must remain true for matching.
- `forbidden_mismatch[]` - mismatches that must block auto-apply in Backend Catalog Matcher.
- `manufacturer_scope` - currently ROSMA-only for this rulebook and fixture family.
- `related_component_suggestions[]` - recommendations only, never confirmed business positions.

Critical fields must not be inferred without evidence from the line or controlled context. If a critical field is absent, the agent should mark it as unknown, ask a clarification question, and keep the output as candidate data.

## Needs Review Rules

The Product Selector Agent does not approve a RequestPosition lifecycle state directly. It signals uncertainty through `needs_clarification`, `clarification_questions[]`, low confidence, `validation_hints`, `must_have[]`, and `forbidden_mismatch[]`. Backend validation then decides whether the affected RequestPosition should move to `needs_review`.

Backend should treat Product Selector output as requiring `needs_review` when:

- a critical field is missing or marked unknown;
- two critical fields contradict each other;
- range, unit, connection, or accuracy class can be interpreted in more than one way;
- product type could be main product or accessory;
- analog permission is implied but not explicit;
- `forbidden_mismatch[]` is non-empty;
- the output includes low confidence for product family, range, connection, quantity, or unit;
- the agent emits unexpected fields or attempts to approve catalog data;
- backend schema or business validation raises AgentRun validation errors.

`needs_review` is a safe outcome. It is preferred over invented model, range, thread, manufacturer, material, option, or catalog identifiers.

## Test Categories

Evaluation must cover at least these categories:

- pressure gauge / манометр;
- vacuum gauge / вакуумметр;
- pressure transducer / датчик давления;
- accessories / доп. оборудование;
- quantity and unit extraction;
- ranges and units;
- thread/connection parsing;
- accuracy class parsing;
- material/execution/options parsing;
- analog request detection;
- ambiguous or incomplete product line;
- forbidden mismatch detection.

Future automated fixtures should tag every test case with one or more categories so quality reports can show weakness by product family and field type.

## Rulebook and Related Component Fixture Coverage

Future fixtures must also verify:

- ROSMA-only manufacturer scope for current Product Selector rulebook behavior;
- future manufacturer extension boundary, including Manotomm, Fiztech, WIKA, Kabeltec, and other future adapters;
- `manufacturer_scope=ROSMA` for ROSMA rulebook cases;
- `rosma_model_candidate` as candidate search text, not final catalog approval;
- `related_component_suggestions[]` shape and required fields;
- related component recommendations for gauges, thermometers, pressure transducers, and diaphragm seals;
- duplicate suppression when bushing, thermowell, hydrofilling, or valve is already present in source request;
- conflict warning instead of duplicate recommendation when an explicit related component has incompatible parameters;
- hydrofilling as a separate related `service_position`, not only as a note in the parent position;
- hydrofilling quantity policy defaulting to parent quantity;
- hydrofilling fluid clarification when glycerin/silicone is not specified;
- no related component recommendation when the parent series/execution does not support it;
- Product Selector never adding related components to invoice, commercial proposal, PDF, or confirmed RequestPosition by itself.

These checks remain future fixture requirements only. This task does not add fixture files or an evaluation runner.

## Test Case Format

Future fixtures can be derived from this structure:

```json
{
  "case_id": "ps-eval-demo-001",
  "categories": ["pressure_gauge", "range", "connection", "accuracy_class"],
  "input": {
    "source_text": "Synthetic product line only",
    "context_refs": ["demo-mail-reader-output-ref"]
  },
  "expected": {
    "must_extract": {
      "intent.product_type": "pressure_gauge",
      "intent.range": "0-10 bar",
      "intent.connection": "G1/2",
      "intent.accuracy_class": "1.5",
      "intent.quantity": 2,
      "intent.unit": "pcs"
    },
    "must_not_include": ["catalog_item_id", "price", "vat", "model_path"],
    "must_set_needs_clarification": false
  },
  "review": {
    "human_review_required": false,
    "critical_failure_if_wrong": ["intent.range", "intent.connection"]
  }
}
```

This is an example fixture shape only. This task does not add executable fixture files.

## Evaluation Examples

All examples are synthetic and must not be treated as real customer data.

| Case | Category | Input line | Expected behavior |
| --- | --- | --- | --- |
| Clean line with all key parameters | pressure gauge / манометр | `Манометр 0-10 bar, G1/2, class 1.5, radial, stainless case, 2 pcs` | Extract product_type pressure_gauge, range `0-10 bar`, connection `G1/2`, accuracy `1.5`, execution `radial`, material hint, quantity `2`, unit `pcs`; no catalog approval. |
| Dirty client-style line | pressure gauge / манометр | `Нужно пару манометров примерно до 10 бар, резьба кажется полдюйма, обычные, можно варианты` | Extract likely pressure_gauge and quantity `2`; mark uncertain thread/range normalization; `analog_request.allowed=true`; ask clarification if thread is not explicit. |
| Line with missing thread | pressure transducer / датчик давления | `Датчик давления 0-16 bar, 4-20 mA, accuracy 0.5, 3 pcs` | Extract product_type pressure_transducer, range, output option, accuracy, quantity; set `needs_clarification=true` because connection/thread is missing. |
| Line with conflicting range/unit | vacuum gauge / вакуумметр | `Вакуумметр -1..0 bar 0..10 bar G1/4 1 шт` | Detect conflicting ranges; add forbidden mismatch / validation hint; set `needs_clarification=true`; do not choose one range silently. |
| Line requesting analog | pressure gauge / манометр | `Манометр 0-6 bar G1/2 class 1.5, если нет такого - предложите аналог` | Extract analog request allowed; keep original must-have fields; analog must remain explicitly marked for Backend Catalog Matcher. |
| Accessory, not main product | accessories / доп. оборудование | `Сифонная трубка для манометра, G1/2, нержавейка, 5 шт` | Classify as accessory, not pressure gauge; extract connection/material/quantity; avoid main product assumptions. |
| Needs review rather than inventing | ambiguous or incomplete product line | `Нужен датчик как в прошлый раз, 2 штуки` | Extract quantity only; mark product_type and critical fields unknown; set `needs_clarification=true`; ask questions; do not invent model, range, connection, or manufacturer. |

Additional future examples should include mixed Cyrillic/Latin abbreviations, decimal separators, MPa/bar/kPa conversion risks, axial/radial wording, explosion-proof options, manufacturer/model-like strings, related component recommendations, duplicate suppression, and hydrofilling as a service-position.

## Pass Criteria

A case passes when all applicable conditions are true:

- Output is valid JSON in the shared LLM envelope.
- Required envelope fields are present.
- Required Product Selector payload fields are present.
- Critical fields that are explicit in the input are extracted correctly.
- Missing critical fields are represented as unknown, clarification questions, or `needs_clarification=true`.
- Contradictory critical fields produce validation hints or `needs_clarification=true`.
- `analog_request` is correct when the input requests or rejects analogs.
- Accessories are not misclassified as main products.
- `must_have[]` preserves explicit customer constraints.
- `forbidden_mismatch[]` captures mismatches that should block backend auto-apply.
- `manufacturer_scope` follows the current ROSMA-only rulebook scope.
- Related component suggestions are recommendations only and include required fields.
- Duplicate related components are suppressed or marked as already present.
- Hydrofilling is represented as separate related service-position when applicable.
- Output does not include final catalog approval, `catalog_item_id`, price, VAT, totals, secrets, credentials, model paths, or real customer data.
- The output can be consumed by backend validation and later by Backend Catalog Matcher as candidate input.

## Fail Criteria

A case fails when any of these conditions occur:

- Output is not parseable JSON.
- Shared envelope is missing or uses unsupported field names.
- Product Selector payload omits required fields without marking review/clarification.
- The agent fabricates missing manufacturer, model, range, connection, accuracy class, material, execution, or options.
- The agent silently resolves contradictory ranges or units without review.
- The agent approves a catalog item or returns a final `catalog_item_id`.
- The agent calculates or invents prices, VAT, totals, discounts, delivery terms, or document values.
- The agent misclassifies an accessory as a main product or a main product as an accessory.
- The agent misses an explicit analog request or invents analog permission when not requested.
- The agent fails to flag a critical mismatch that should block auto-apply.
- The agent applies ROSMA-specific rules as universal rules for another manufacturer.
- The agent duplicates bushing, thermowell, hydrofilling, or valve suggestions already present in the request.
- The agent represents hydrofilling only as parent note when a separate service-position suggestion is required.
- The agent emits secrets, credentials, private keys, full prompts, filesystem model paths, production emails, or real customer data.

## Quality Metrics

Future quality reports should group metrics by `model_name`, `prompt_version`, `agent_version`, test category, and critical field.

Recommended metrics:

- JSON validity rate.
- Shared envelope completeness rate.
- Required payload field completeness rate.
- Critical field precision and recall.
- Quantity extraction accuracy.
- Unit normalization accuracy.
- Range parsing accuracy.
- Thread/connection parsing accuracy.
- Accuracy class parsing accuracy.
- Material/execution/options extraction accuracy.
- Analog request detection precision and recall.
- Forbidden mismatch detection recall.
- Hallucination rate for missing critical fields.
- `needs_review` calibration: false negatives and false positives.
- Accessory classification accuracy.
- Related component recommendation precision.
- Duplicate suppression accuracy.
- Hydrofilling service-position extraction accuracy.
- Manufacturer scope accuracy.
- Manager correction rate.
- Overall fixture pass rate.

Exact numeric thresholds are deferred until the first fixture set is approved by the product owner and technical reviewer.

## Human Review Rules

Human review is required when:

- any critical field is missing, ambiguous, or contradictory;
- confidence is low for range, connection, product type, or quantity;
- product family classification is unclear;
- analog permission is unclear;
- accessory vs main product classification is unclear;
- unit conversion could change product compatibility;
- forbidden mismatch is detected;
- related component suggestion has missing or conflicting parent parameters;
- hydrofilling fluid type is missing or parent support is unclear;
- manufacturer scope is not ROSMA under current rulebook;
- the model returns unexpected fields;
- backend validation reports `invalid_json`, `missing_required_field`, `invalid_quantity`, `invalid_unit`, `low_confidence`, `ambiguous_position`, or `critical_mismatch`;
- the output would influence catalog matching, documents, CRM, or 1C exchange.

Human review must not turn raw LLM output directly into business data. Review decisions should be recorded through AgentRun quality fields when backend implementation exists.

## Non-Fabrication Rules

The model must not invent:

- manufacturer;
- series;
- model;
- range;
- connection/thread;
- accuracy class;
- material;
- execution;
- options;
- quantity;
- unit;
- analog permission;
- related component model;
- catalog item IDs;
- prices, VAT, totals, discounts, delivery terms, or legal document values.

If a value is missing or uncertain, the output should use an unknown/empty candidate value, `needs_clarification=true`, a clarification question, and a safe `next_action` such as `backend_validation` or `manager_review`.

## Known Risks

- The `latest` model tag can drift; future quality records should capture model metadata available from the runtime without using filesystem paths.
- Synthetic examples may not cover all real wording patterns, abbreviations, and noisy mail content.
- Unit normalization can hide dangerous mismatches if backend validation is weak.
- Product families may share similar wording, especially gauges, sensors, and accessories.
- Analog requests can be implied in natural language and may require manager review.
- ROSMA-only rules can become harmful if applied to other manufacturers without adapters.
- Related component suggestions may over-suggest unless duplicate suppression and confirmation are enforced.
- Without Backend Catalog Matcher, evaluation can only judge intent extraction quality, not final catalog matching.
- The first fixture set needs product-owner review before numeric thresholds become binding.

## Conversion to Automated Evaluation Fixtures

A later task can convert this plan into automated fixtures by:

- creating fixture files with synthetic inputs and expected candidate JSON;
- tagging each fixture with categories and critical fields;
- adding expected pass/fail assertions for schema, field extraction, related recommendations, duplicate suppression, manufacturer scope, and non-fabrication;
- recording `model_name`, `prompt_version`, `agent_version`, and fixture set version;
- running the model through a controlled backend evaluation runner;
- storing raw output by reference and normalized output through AgentRun-like records;
- producing quality reports by category and validation error code.

That later task must still keep backend validation mandatory and must not allow Product Selector output to approve catalog items or related components directly.

## Acceptance Criteria Checklist

- Model name is documented as `artmatica-product-selector-gemma:latest`.
- No filesystem model path is used.
- No real secrets, credentials, production emails, or customer data are included.
- Expected output stays candidate data.
- Backend validation remains mandatory.
- Product Selector is not allowed to approve catalog items.
- Product Selector is not allowed to calculate prices.
- Product Selector is not allowed to fabricate missing critical parameters.
- Product Selector is not allowed to apply ROSMA-only rules universally.
- The plan can later be converted into automated evaluation fixtures.

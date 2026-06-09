# Product Selector Rulebook

This document distills Product Selector Agent rules from the legacy ROSMA prompt into ArtCRM documentation. It intentionally excludes old Flask, Yandex AI Studio, SQLite, dashboard, route, upload form, Excel stock lookup, and legacy UI implementation requirements.

This is documentation only. It does not call Ollama, modify `artmatica-product-selector-gemma:latest`, create fixtures, create an evaluation runner, add backend/frontend code, add dependencies, or change `.env.example`.

## Purpose

Product Selector Agent / CRM Position Intent Agent converts one raw request position into structured candidate intent for backend validation and later Backend Catalog Matcher processing.

The agent may:

- normalize rough product text;
- identify a candidate product family;
- build a ROSMA model-name candidate when the scope is ROSMA;
- extract range, connection, quantity, material, execution, options, and analog intent;
- identify missing fields and warnings;
- suggest related components as candidate recommendations.

The agent must not:

- approve `catalog_item_id`;
- calculate prices, VAT, totals, discounts, delivery terms, or lead times;
- generate invoices, commercial proposals, or PDFs;
- send email;
- write business data directly;
- fabricate missing critical parameters.

All output is candidate data. Backend validation is mandatory before any candidate value can affect RequestCard, RequestPosition, CatalogItem, Deal, documents, 1C exchange, or customer-facing output.

## Current Manufacturer Scope

Current Product Selector scope is ROSMA only.

ROSMA rules in this document are manufacturer-specific rules. They must not be treated as universal rules for Manotomm, Fiztech, WIKA, Kabeltec, or other manufacturers.

Required scope markers:

- `manufacturer_scope`: `ROSMA` for rules in this document.
- `intent.manufacturer`: `ROSMA` when the line is interpreted as ROSMA product intent.
- `rosma_model_candidate`: candidate ROSMA naming string or an unknown/partial value.
- `warnings[]`: must include scope warnings when the source line appears to request another manufacturer.
- `needs_clarification`: true when manufacturer scope is unclear or non-ROSMA analog handling is ambiguous.

If a customer explicitly asks for a non-ROSMA product, Product Selector may identify the requested manufacturer and capture an analog request, but it must not pretend that ROSMA naming rules are native to that manufacturer.

## Future Manufacturer Extension

Future manufacturers must be added through separate manufacturer-specific rulebooks, adapters, or rulesets. Expected future targets include Manotomm, Fiztech, WIKA, Kabeltec, and other manufacturers.

Future extension rules:

- Each manufacturer must have its own naming conventions.
- A manufacturer adapter must declare supported product families and critical fields.
- Cross-manufacturer analog mapping must remain explicit candidate data.
- Unsupported manufacturer rules must route to `needs_clarification` or manager review.
- ROSMA defaults must not leak into non-ROSMA matching.
- Evaluation fixtures must tag manufacturer scope.

## Legacy Field Mapping

Legacy prompt fields are mapped into ArtCRM Product Selector contract as follows:

| Legacy field | ArtCRM target | Notes |
| --- | --- | --- |
| `type` | `intent.product_type` | Normalize to current product taxonomy. Legacy values were mixed product categories and service categories. |
| `model` | `rosma_model_candidate` and `search.main_query` | Candidate ROSMA name for search, not final catalog item. |
| `range` | `intent.range` | Keep as candidate normalized measurement range. Backend validates unit and catalog compatibility. |
| `connection` | `intent.connection` | Thread/process connection candidate. Must not be invented. |
| `qty` | `intent.quantity` | Quantity candidate. Default can be `1` only when the request gives no other quantity and product semantics allow it. |
| `note` | `warnings[]`, `missing_fields[]`, `clarification_questions[]`, `structured_intent.notes` | Do not hide critical service positions only in notes. |
| `needs_clarification` | `needs_clarification`, `missing_fields[]`, `warnings[]` | Backend decides RequestPosition lifecycle after validation. |

Legacy prompt sometimes placed service work, such as hydrofilling, in `note`. ArtCRM overrides this for Product Selector: hydrofilling must be represented as a separate related service-position suggestion, not only as a note.

## ArtCRM Candidate Fields

Product Selector should produce the shared envelope from [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md). The payload may include these ROSMA-specific candidate fields:

- `manufacturer_scope` - current rule scope, `ROSMA` for this rulebook.
- `rosma_model_candidate` - candidate ROSMA naming string.
- `structured_intent` - normalized product intent derived from source text.
- `must_have[]` - explicit customer constraints that matching must preserve.
- `forbidden_mismatch[]` - mismatches that must block backend auto-apply.
- `missing_fields[]` - critical fields absent from source/context.
- `warnings[]` - non-secret warnings for manager/backend review.
- `analog_request` - whether customer requested analog handling and why.
- `related_component_suggestions[]` - candidate related components or service-position suggestions.

All fields are candidate data. Backend validation remains the source of truth.

## ROSMA Model Candidate Rules

`rosma_model_candidate` is a candidate normalized ROSMA string for search and review. It is not `catalog_item_id` and not an approved match.

Distilled ROSMA naming conventions:

- Use ROSMA naming style for recognized ROSMA product families only.
- Preserve a structured order for instrument names: model/type, series or execution, range in parentheses, connection, accuracy class, then options when applicable.
- Pressure units in ROSMA naming candidates should use catalog-style units such as `MPa` and `kPa` when normalization is safe.
- Decimal separator in ROSMA-style values should use comma when following ROSMA naming convention.
- Temperature ranges should preserve Celsius notation when applicable.
- Thread notation must be normalized carefully, for example `G1/2`, `M20x1,5`, `M12x1,5`, `NPT1/2`.
- Range belongs in parentheses in ROSMA model candidates when the product family uses that format.
- Connection follows the range without becoming a separate final catalog approval.
- Accuracy class is a critical field when the family requires it.
- Options such as IP protection, oxygen/ammonia execution, red scale, control pointer, or filling must remain candidate options and require backend validation.

Do not fabricate ROSMA model names when critical fields are missing. Use partial candidate strings, `missing_fields[]`, `warnings[]`, and clarification questions instead.

## Structured Intent Rules

`structured_intent` should keep a normalized representation separate from the ROSMA naming candidate.

Recommended fields:

```json
{
  "manufacturer_scope": "ROSMA",
  "source_text": "synthetic source line",
  "rosma_model_candidate": "candidate ROSMA name or unknown",
  "structured_intent": {
    "product_type": "pressure_gauge",
    "manufacturer": "ROSMA",
    "series": "candidate series or unknown",
    "model": "candidate base model or unknown",
    "range": "candidate range or unknown",
    "connection": "candidate connection or unknown",
    "accuracy_class": "candidate accuracy or unknown",
    "material": "candidate material or unknown",
    "execution": "candidate execution or unknown",
    "options": [],
    "quantity": 1,
    "unit": "pcs"
  },
  "missing_fields": [],
  "warnings": [],
  "must_have": [],
  "forbidden_mismatch": [],
  "analog_request": {
    "allowed": false,
    "source_text": "",
    "reason": "No explicit analog request"
  }
}
```

## Must-Have Rules

`must_have[]` must capture explicit customer requirements that cannot be changed by analog matching or related-component suggestions.

Examples:

- product type;
- pressure or temperature range;
- connection/thread;
- accuracy class when stated;
- material when stated;
- execution such as radial, axial, vibration-resistant, corrosion-resistant, oxygen, ammonia, IP level;
- output signal for pressure transducers;
- thermowell length or thermometer immersion length;
- customer explicitly requiring or rejecting analogs.

If a requested analog violates `must_have[]`, Product Selector must add `forbidden_mismatch[]` or warning rather than silently altering the request.

## Forbidden Mismatch Rules

`forbidden_mismatch[]` must capture mismatches that should block backend auto-apply and force review.

Common forbidden mismatches:

- wrong product family;
- wrong manufacturer scope;
- pressure/vacuum/manovacuum confusion;
- incompatible range or unit conversion uncertainty;
- wrong connection/thread;
- wrong accuracy class when required;
- material conflict, such as customer asks stainless but candidate is steel;
- radial/axial/execution conflict;
- unsupported flange or mounting execution;
- hydrofilling requested for a series/execution that does not support it;
- accessory suggested as main product or main product suggested as accessory.

## Missing Fields Rules

`missing_fields[]` must list critical absent fields. Missing critical fields should also drive `needs_clarification=true` or manager review.

Typical missing fields:

- product family;
- range;
- connection/thread;
- quantity;
- unit;
- accuracy class when required;
- output signal for pressure transducer;
- material or execution when customer intent depends on it;
- thermometer series or insertion length when thermowell is requested;
- analog permission when the customer wording is ambiguous.

## Warning Rules

`warnings[]` should contain safe, non-secret review warnings. It must not contain full prompts, credentials, production emails, or sensitive customer data.

Useful warnings:

- possible non-ROSMA manufacturer detected;
- partial ROSMA model candidate only;
- range normalized from bar/kgf/cm2 and needs backend validation;
- connection inferred from ambiguous wording;
- related component already appears in request with conflicting parameters;
- hydrofilling requested but fluid type is missing;
- requested combination may not exist in ROSMA catalog;
- manager should confirm related component recommendation.

## Analog Request Rules

`analog_request` captures whether the customer is asking for analog handling.

Rules:

- Explicit wording like "предложите аналог" should set analog allowed.
- Non-ROSMA manufacturer/model references should be captured as candidate analog context, not final ROSMA approval.
- If a direct ROSMA analog is not clear, mark `needs_clarification=true` and explain the ambiguity in `warnings[]`.
- Do not hide analog substitution in `rosma_model_candidate`; keep original requested manufacturer/model in candidate context where safe.
- Analog suggestions must preserve `must_have[]` constraints.
- Product Selector must not decide that an analog is approved for commercial offer.

## Product Family Distilled Rules

### Pressure Gauges, Vacuum Gauges, Manovacuum Gauges

- Recognize pressure gauge / манометр, vacuum gauge / вакуумметр, and manovacuum gauge / мановакуумметр as different product families.
- Extract range sign and unit carefully.
- Do not silently convert contradictory pressure ranges.
- Connection is critical and must not be invented when absent.
- Radial/axial wording is execution data and may affect ROSMA candidate model.
- Hydrofilling is a related service-position suggestion, not a model code hidden in the main position.

### Thermometers

- Extract thermometer family, series, range, connection, insertion length, and execution.
- If customer requests a thermometer with thermowell, keep the thermometer as the parent position and represent thermowell as a separate related component suggestion.
- Do not duplicate a thermowell recommendation if the thermowell is already explicitly present.

### Pressure Transducers

- Extract measured pressure type, range, output signal, connection, accuracy class, electrical connection if present, and special execution.
- Output signal is critical for transducers.
- Related recommendations may include bushing, adapter, needle valve, diaphragm seal, or cooler when applicable, but only as recommendations.

### Diaphragm Seals

- Extract seal family, process connection, instrument connection, size/execution, and media/filling context if present.
- Opposite/answer part, assembly with instrument, and filling liquid are related positions or service-position candidates, not automatic approved lines.

### Accessories and Service Positions

- Accessories must be classified as accessories, not as main products.
- Service positions must remain linked to parent positions and require backend validation.
- If a service or accessory is already requested explicitly, do not suggest it again.

## Grouping and Quantity Rules

Product Selector may identify likely duplicate raw lines, but backend owns final grouping.

Candidate grouping rules:

- same product family and same candidate ROSMA model can be marked as duplicate candidates;
- quantities can be summed only as candidate data;
- warnings should mention grouping when source lines were combined;
- related component quantity should normally follow parent quantity unless customer gives a different explicit quantity;
- backend validation must confirm all grouping before business records change.

## Non-Fabrication Rules

Product Selector must not invent:

- ROSMA model;
- manufacturer;
- series;
- range;
- connection/thread;
- accuracy class;
- material;
- execution;
- option;
- quantity;
- analog permission;
- related component model;
- catalog item ID;
- price, VAT, total, delivery term, invoice data, commercial proposal data, or PDF content.

Use `missing_fields[]`, `warnings[]`, `needs_clarification=true`, `clarification_questions[]`, and manager/backend review instead.

## Backend Validation Boundary

Backend validation must check:

- shared envelope schema;
- Product Selector payload schema;
- `manufacturer_scope`;
- candidate ROSMA naming shape;
- critical fields and missing fields;
- related component recommendation fields;
- duplicate suppression flags;
- analog request consistency;
- no prohibited financial/document/email fields;
- no secrets, credentials, private keys, production emails, model paths, or full prompts.

Product Selector output can support Backend Catalog Matcher input only after backend validation.

## Deferred Decisions

Deferred to future tasks:

- machine-enforced JSON Schema files;
- manufacturer adapter registry;
- exact ROSMA catalog validation tables;
- automated fixtures;
- evaluation runner;
- Backend Catalog Matcher implementation;
- related-component recommendation UI;
- persistence schema for related component suggestions.

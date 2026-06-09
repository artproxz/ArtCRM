# Product Selector Evaluation Fixtures

This document describes the documentation-only fixture base for future quality evaluation of the Product Selector Agent.

The model under future test is `artmatica-product-selector-gemma:latest`, but these fixtures do not call Ollama, do not execute the model, do not update a Modelfile, and do not create an evaluation runner.

## Purpose

The fixture base defines synthetic input lines and expected candidate outputs before Product Selector model changes or backend integration. It gives the product owner, technical reviewer, and future evaluation runner a stable reference for judging whether the model extracts industrial product intent safely.

The fixture base checks that Product Selector:

- extracts product intent from synthetic ROSMA-oriented request lines;
- marks uncertain or incomplete critical fields for review;
- keeps all LLM output as candidate data;
- leaves final catalog matching to backend services;
- suggests related components only as recommendations;
- suppresses duplicate related component recommendations when the component is already present;
- represents hydrofilling as a separate related service-position when applicable.

## Scope

The machine-readable fixtures are stored in [product_selector_eval_fixtures.json](fixtures/product_selector_eval_fixtures.json).

All fixture inputs are synthetic. They are not real customer requests, production emails, secrets, credentials, tokens, passwords, private keys, model paths, or production data.

Expected outputs are expected candidate data. Backend validation remains mandatory before any value can affect RequestPosition, CatalogItem, documents, CRM, or 1C exchange.

## Relationship to Existing Documents

These fixtures are derived from and should be reviewed together with:

- [Product Selector Agent Quality Evaluation Plan](PRODUCT_SELECTOR_EVAL.md);
- [Product Selector Rulebook](PRODUCT_SELECTOR_RULEBOOK.md);
- [Product Selector Related Component Rules](PRODUCT_SELECTOR_RELATED_COMPONENTS.md);
- [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md).

The rulebook defines ROSMA-specific Product Selector behavior. The related component rules define recommendation boundaries. The JSON schema document defines the shared LLM output envelope and Product Selector payload shape.

## Fixture Format

Each fixture contains:

- `id` - stable fixture identifier;
- `category` - one or more coverage categories;
- `manufacturer_scope` - current rulebook scope, expected to be `ROSMA` for this fixture set;
- `input_text` - synthetic source line or grouped source lines;
- `expected_output` - expected candidate JSON shape for Product Selector output;
- `expected_related_component_suggestions` - expected recommendations or suppression records;
- `critical_fields` - fields that are unsafe to invent or ignore;
- `forbidden_actions` - actions the Product Selector must not perform;
- `expected_warnings` - warnings expected from this fixture;
- `expected_needs_review` - whether backend should route the case to review;
- `notes` - human-readable review notes.

The fixture JSON is intentionally an evaluation artifact, not an API implementation. Field names are aligned with the documented contracts, but executable assertion logic is deferred to a later task.

## Coverage Summary

The first fixture set includes 23 synthetic cases covering:

- pressure gauge / манометр;
- vacuum gauge / вакуумметр;
- manovacuum gauge / мановакуумметр;
- bimetal thermometer / термометр биметаллический;
- pressure transducer / датчик давления;
- diaphragm seal / разделитель сред;
- bushing / бобышка;
- thermowell / гильза;
- three-way valve / кран трехходовой;
- needle valve / клапан игольчатый;
- adapter / переходник;
- loop tube / трубка петлевая;
- hydrofilling as a service-position;
- dirty client-style wording;
- missing thread;
- missing accuracy class;
- conflicting range or unit;
- requested analog;
- accessories already present in the request;
- thermowell already present in the request;
- bushing already present in the request;
- hydraulic filling already present in the request;
- related component duplicate suppression;
- unsupported or impossible combinations;
- cases where the model must set `needs_review` instead of inventing data.

## Related Component Coverage

The fixtures cover recommendation behavior for:

- pressure gauges: bushing, three-way valve, and hydrofilling service-position;
- thermometers: thermowell and bushing;
- pressure transducers: bushing, adapter, needle valve, and diaphragm seal;
- diaphragm seals: mating part, assembly with instrument, and filling liquid service-position.

Every related component suggestion must include a parent position reference, reason, quantity policy, confirmation flag, and backend validation flag. Product Selector can recommend these items, but it cannot add them as confirmed RequestPositions, commercial proposal lines, invoice lines, or PDF lines.

## Duplicate Suppression

Duplicate suppression is expected when the source request already includes a related component. The fixture set includes cases where bushing, thermowell, hydrofilling, and three-way valve are already present.

If a related component is present but conflicts with the parent parameters, the expected behavior is not to duplicate it. The Product Selector should mark a warning or review requirement so backend validation and a manager can resolve the conflict.

## Hydrofilling as Service-Position

Hydrofilling is represented as a separate related service-position, not only as a note inside the parent pressure gauge.

Default behavior:

- quantity follows the parent gauge quantity;
- the recommendation keeps a parent position reference;
- manager or customer confirmation is required;
- backend validation is mandatory;
- if fluid type is missing, the expected `question_to_manager` is: `Уточнить тип гидрозаполнения: глицерин или силикон?`.

Example expected recommendation text:

`Гидрозаполнение глицерином для манометра диам.100 — 5 шт.`

## Future Runner Boundary

A later task may create an automated evaluation runner that:

- reads `docs/fixtures/product_selector_eval_fixtures.json`;
- calls the model in a controlled environment;
- validates the shared LLM envelope;
- compares extracted fields, warnings, related component suggestions, duplicate suppression, and review flags;
- records results by `model_name`, `prompt_version`, `fixture_set`, and category.

That later runner must still keep Product Selector output as candidate data and must not bypass backend validation.

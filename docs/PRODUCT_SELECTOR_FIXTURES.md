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

The first fixture set includes 26 synthetic cases covering:

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
- missing thermometer immersion length;
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

## Hydrofilling as Service-Position

Hydrofilling is represented as a separate related service-position, not only as a note inside the parent pressure gauge.

Positive hydrofilling fixtures must use hydrofillable ROSMA series 20 or 21, such as `ТМ-520Р` or `ТМ-521Р`. Series 10 / general-purpose `ТМ-510Р` is covered by a negative fixture and must not produce a valid ready recommendation for hydrofilling.

Default behavior:

- quantity follows the parent gauge quantity;
- the recommendation keeps a parent position reference;
- manager or customer confirmation is required;
- backend validation is mandatory;
- if fluid type is `глицерин`, the expected service-position text is `Гидрозаполнение глицерином для манометра диам.100 — N шт.`;
- if fluid type is `силикон`, the expected service-position text is `Гидрозаполнение силиконом для манометра диам.100 — N шт.`;
- if fluid type is missing, the expected `question_to_manager` is: `Уточнить тип гидрозаполнения: глицерин или силикон?`.

If a customer asks for hydrofilling on `ТМ-510Р` / series 10, the expected behavior is:

- no valid service-position recommendation;
- `expected_needs_review=true`;
- warning `hydrofilling_not_supported_for_series_10`;
- manager clarification asking to check the series or vibration-resistant execution;
- no silent parent model change from `ТМ-510Р` to `ТМ-520Р` or `ТМ-521Р`.

## Thermowell Selection

Thermowell suggestions are not based only on whether a thermometer is `211` or `220`. They are candidate recommendations built from explicit product parameters and must remain subject to backend validation and confirmation.

Thermowell selection must consider:

- thermometer series: `211`, `220`, `ТТ-В`, or `РТ-1`;
- immersion length `L`;
- thermowell diameter `d`;
- connection type;
- material.

Fixture rules:

- thermowell `L` must equal the thermometer immersion length;
- if `L` is missing, a confident thermowell recommendation is not allowed;
- for series `211`, expected `d=10` and an outer thread such as `G1/2` or `M20x1,5`;
- for series `220`, expected `d=14` by default or `d=16` for 60 MPa, and a thread pair such as `G1/2-G1/2`;
- for `ТТ-В`, expected `d=10`;
- for `РТ-1`, expected `d=15` and only `L=125`.

The fixture `psf-004-bimetal-thermometer-related-components` keeps a thermowell recommendation for `БТ-51.211` because the input contains `L=64` and no separate thermowell line. The expected candidate is:

`Гильза для термометра xx.211 L=64мм, d=10, G1/2, нерж. Китай`

The fixture `psf-020-thermowell-already-present` suppresses a duplicate thermowell recommendation because a thermowell is already explicitly present in the request.

The fixture `psf-026-thermometer-missing-immersion-length` expects `needs_review=true`, `missing_fields` containing `length` / `immersion_length`, and this manager question:

`Уточнить длину погружной части термометра для подбора гильзы.`

## Duplicate Suppression

Duplicate suppression is expected when the source request already includes a related component. The fixture set includes cases where bushing, thermowell, hydrofilling, and three-way valve are already present.

If a related component is present but conflicts with the parent parameters, the expected behavior is not to duplicate it. The Product Selector should mark a warning or review requirement so backend validation and a manager can resolve the conflict.

## Thread Normalization

Normalized thread output must use Latin letters for thread notation. For example, even if source text contains Cyrillic `М20х1,5`, expected normalized values use `M20x1,5`.

Fixture `psf-012-loop-tube-thread-normalization` checks that `rosma_model_candidate`, `structured_intent.connection`, and `must_have[]` use Latin `M` and `x`.

## Future Runner Boundary

A later task may create an automated evaluation runner that:

- reads `docs/fixtures/product_selector_eval_fixtures.json`;
- calls the model in a controlled environment;
- validates the shared LLM envelope;
- compares extracted fields, warnings, related component suggestions, duplicate suppression, and review flags;
- records results by `model_name`, `prompt_version`, `fixture_set`, and category.

That later runner must still keep Product Selector output as candidate data and must not bypass backend validation.

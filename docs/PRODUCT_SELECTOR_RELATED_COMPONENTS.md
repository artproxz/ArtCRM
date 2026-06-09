# Product Selector Related Component Rules

This document defines documentation-only rules for related component and service-position suggestions produced by Product Selector Agent. It is based on distilled Product Selector-relevant legacy ROSMA behavior and ArtCRM safety boundaries.

This document does not call Ollama, modify the model, create fixtures, create an evaluation runner, add backend/frontend code, add dependencies, or change `.env.example`.

## Core Rules

Related positions are recommendations only.

Product Selector may suggest a related component or service-position, but it must not add it to a commercial proposal, invoice, RequestCard, RequestPosition, PDF, email, or 1C exchange as confirmed business data.

Every related suggestion requires:

- backend validation;
- manager or customer confirmation;
- link to a parent position;
- explicit reason;
- explicit quantity policy;
- duplicate suppression check;
- safe warning or review path when parameters conflict.

Required fields for every related recommendation:

- `relation_type`
- `suggested_type`
- `suggested_model_candidate`
- `parent_position_ref`
- `reason`
- `quantity_policy`
- `quantity_candidate`
- `requires_confirmation`
- `already_present_in_request`
- `backend_validation_required`
- `question_to_manager`
- `manufacturer_scope`
- `future_manufacturer_extension_notes`

Suggested values remain candidate data.

## Confirmation Boundary

A related component can become a business position only after:

1. Product Selector proposes it as candidate recommendation.
2. Backend validation checks schema, scope, parent link, duplicate status, and critical parameters.
3. Manager or customer confirms the recommendation.
4. Backend creates or updates draft RequestPosition according to future business workflow.

Product Selector must not bypass this flow.

## Duplicate Suppression

If a related component is already explicitly present in the customer request, Product Selector must not suggest it again.

Duplicate suppression rules:

- If the request already includes a bushing, do not suggest another bushing for the same parent position.
- If the request already includes a thermowell, do not suggest another thermowell for the same thermometer.
- If the request already includes hydrofilling, do not suggest hydrofilling again.
- If the request already includes a three-way valve or needle valve, do not suggest another valve for the same parent position.
- If the request includes the related component but parameters conflict, do not duplicate it. Set `already_present_in_request=true`, add warning, and route to `needs_review`.
- Duplicate detection is candidate-only; backend validation owns final duplicate decision.

## Quantity Policy

Default quantity policy:

- `same_as_parent` when one related component is normally needed per parent item.
- `explicit_customer_quantity` when customer gives a different quantity.
- `manager_review` when quantity depends on installation scheme or missing context.

Examples:

- 5 pressure gauges -> 5 bushings if bushing is recommended.
- 5 pressure gauges -> 5 three-way valves if valve is recommended.
- 5 pressure gauges with hydrofilling -> 5 hydrofilling service positions.
- 2 thermometers with thermowells -> 2 thermowells unless customer says otherwise.

Product Selector must not calculate pricing or delivery terms for related positions.

## Pressure Gauge Recommendations

For pressure gauges, Product Selector may recommend candidate related positions when they are not already present in the request.

Recommended candidates:

- Bushing under the instrument connection, for example: `Бобышка БП-ТМ-30-G1/2` - same quantity as parent.
- Three-way valve under the instrument connection, for example: `Кран трехходовой G1/2` - same quantity as parent.
- Hydrofilling as a separate service-position, for example: `Гидрозаполнение глицерином для манометра диам.100` - same quantity as parent when supported.

Rules:

- Use parent `connection` to form bushing or valve candidate.
- If connection is missing, do not invent it. Ask a question.
- If the parent series/execution does not support hydrofilling, do not suggest hydrofilling.
- If customer already requested bushing, valve, or hydrofilling, suppress duplicate suggestion.
- If customer asks for hydrofilling but fluid type is missing, ask whether glycerin or silicone is required.

## Thermometer Recommendations

For thermometers, Product Selector may recommend:

- thermowell under thermometer series, insertion length, and connection;
- bushing under connection.

Rules:

- If customer writes "thermometer with thermowell", thermowell should be represented as a separate related position candidate.
- Do not duplicate thermowell as a recommendation if it already appears as explicit customer position.
- Thermowell recommendation needs thermometer series, insertion length, connection, and material context.
- If length is missing, set `question_to_manager` and route to review.
- Bushing recommendation should follow parent connection when known.

## Pressure Transducer Recommendations

For pressure transducers, Product Selector may recommend:

- bushing under RPD connection;
- adapter;
- needle valve;
- diaphragm seal;
- cooler when high temperature or process conditions imply it.

Rules:

- Connection and pressure/range context are critical.
- Output signal remains part of the parent transducer intent, not a related component.
- Diaphragm seal, cooler, and adapter suggestions require manager review unless explicitly requested.
- Do not suggest a related item if it is already present in the request.

## Diaphragm Seal Recommendations

For diaphragm seals, Product Selector may recommend:

- answer/opposite part;
- assembly with instrument;
- filling liquid as related service-position.

Rules:

- Assembly and filling suggestions are service-position candidates, not note-only fields.
- Link every service suggestion to the parent diaphragm seal or instrument position.
- If filling liquid is missing, ask a clarification question.
- If answer part already appears in the request, suppress duplicate suggestion.

## Hydrofilling as Separate Service-Position

ArtCRM uses the second variant: hydrofilling is a separate related service-position.

It must not be represented only as a note inside the main pressure gauge position.

Required behavior:

- Create a related service-position suggestion, not an approved RequestPosition.
- Preserve `parent_position_ref` to the main gauge candidate.
- Use default quantity equal to parent quantity.
- Set `requires_confirmation=true`.
- Set `backend_validation_required=true`.
- Ask for fluid type when missing: glycerin or silicone.
- Do not suggest hydrofilling if the parent series/execution does not support it.
- Suppress duplicate if hydrofilling is already in the customer request.

Recommended candidate text:

`Гидрозаполнение глицерином для манометра диам.{diameter} - {qty} шт.`

If the fluid is unknown:

- `suggested_model_candidate` may be partial;
- `question_to_manager` should ask: `Уточнить тип жидкости для гидрозаполнения: глицерин или силикон?`;
- backend should keep the related suggestion in review.

## Example Related Suggestion Shape

```json
{
  "relation_type": "service_position",
  "suggested_type": "hydrofilling",
  "suggested_model_candidate": "Гидрозаполнение глицерином для манометра диам.100 - 5 шт.",
  "parent_position_ref": "request-position-candidate-1",
  "reason": "Customer requested glycerin filling for the parent pressure gauge",
  "quantity_policy": "same_as_parent",
  "quantity_candidate": 5,
  "requires_confirmation": true,
  "already_present_in_request": false,
  "backend_validation_required": true,
  "question_to_manager": "",
  "manufacturer_scope": "ROSMA",
  "future_manufacturer_extension_notes": "Hydrofilling support must be checked per manufacturer adapter in future rulebooks."
}
```

## Conflict Handling

When a related item exists in the request but conflicts with parent parameters:

- do not create a duplicate suggestion;
- set `already_present_in_request=true`;
- add warning that parameters conflict;
- set `requires_confirmation=true`;
- set `backend_validation_required=true`;
- backend should move the affected position or suggestion to `needs_review`.

Examples:

- Gauge connection is `G1/2`, but explicit bushing line says `M20x1,5`.
- Thermometer length is `L=64`, but explicit thermowell line says `L=100`.
- Customer requests hydrofilling but parent gauge series does not support it.
- Requested valve connection does not match parent instrument connection.

## Manufacturer Scope

Current related-component rules are ROSMA-specific. They rely on ROSMA/legacy accessory behavior and must not be applied universally.

Future manufacturers must define their own related-component rules. Until then:

- mark non-ROSMA related suggestions as unsupported or review-required;
- do not apply ROSMA bushing/thermowell naming to Manotomm, Fiztech, WIKA, Kabeltec, or other manufacturers;
- keep `future_manufacturer_extension_notes` populated for extension points.

## Backend Validation Checks

Backend validation should later check:

- required related suggestion fields;
- parent position exists and is eligible;
- manufacturer scope is supported;
- related type is allowed for parent product family;
- duplicate status against source request and current draft positions;
- quantity policy and quantity candidate;
- hydrofilling support by parent series/execution;
- no financial/document/email fields;
- no secrets, credentials, model paths, production emails, or real customer data.

## Deferred Decisions

Deferred to future tasks:

- executable fixtures for related component recommendations;
- duplicate detection implementation;
- backend validation implementation;
- manager UI for accepting/rejecting recommendations;
- manufacturer adapter registry;
- exact catalog item validation for suggested related models.

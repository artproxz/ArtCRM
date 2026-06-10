# Catalog Data Model

This document defines the documentation-only catalog foundation for ArtCRM before catalog import, Backend Catalog Matcher, database schema, or application implementation.

It does not add backend code, frontend code, SQL, ORM, migrations, containers, dependencies, model changes, Ollama calls, fixtures runner, `.env.example` changes, source spreadsheets, secrets, credentials, production emails, or filesystem model paths.

## Purpose

ArtCRM catalog data must not be modeled as a flat SKU list only. The normalized catalog layer must support a constructor-style structure:

1. manufacturer;
2. product family;
3. product type;
4. product-type-specific filter profile;
5. series/model;
6. concrete catalog item / SKU;
7. stock and availability as a separate layer;
8. analog and related component rules as separate layers.

This structure lets Product Selector candidate data and Backend Catalog Matcher decisions use the correct filters for each product type. A pressure gauge, thermowell, pressure transducer, and hydrofilling service-position must not share one universal parameter set.

## Scope

Current manufacturer scope is ROSMA.

Future manufacturers, such as Manotom, Fiztech, WIKA, Kabeltec, and others, must be added through manufacturer-specific mapping profiles and adapters. ROSMA naming, grouping, and matching rules must not become universal rules.

## Source Context

Known source classes for future import:

- ROSMA price/catalog files with item rows and group/header rows;
- stock files with catalog codes and stock or availability columns;
- analog tables;
- naming/rule references for series, product types, options, and related components.

Audit notes from ART-36 context:

- catalog source contains about 5,051 item rows and about 729 group/header rows;
- stock source contains matching catalog codes and availability columns;
- major ROSMA groups include vacuum gauges, manovacuum gauges, pressure gauges, thermomanometers, thermometers, accessories, relays/sensors, diaphragm seals, solenoid valves, tender group, and hydrofilling nomenclature.

These source files are reference inputs only. They must not be committed to the repository as part of this documentation task.

## Constructor-Style Catalog Model

Catalog navigation and matching should follow this conceptual order:

```text
Manufacturer
  -> ProductFamily
    -> ProductType
      -> ProductTypeFilterProfile
        -> Series / Model
          -> CatalogItem / SKU
```

The filter profile controls which fields may be used for matching and UI filtering. Fields marked `not_applicable` for a product type must not be shown as UI filters for that product type and must not be required from Product Selector or Backend Catalog Matcher.

Examples:

- `pressure_gauge` uses pressure measurement range, unit, thread, connection type, and accuracy class; `immersion_length` is not applicable.
- `thermowell` uses compatible parent type/series, immersion length, stem diameter, thread or thread pair; `accuracy_class` is not applicable.
- `pressure_transducer` requires `signal_output`; `pressure_gauge` must not require `signal_output`.
- `service_position` such as hydrofilling does not have its own measurement range.

## Normalized Catalog Entities

### Manufacturer

Purpose: identifies a manufacturer-specific catalog source and rule boundary.

Key fields:

- `manufacturer_id`
- `manufacturer_code`
- `display_name`
- `country_candidate`
- `source_profile`
- `status`

### ProductFamily

Purpose: groups related product types under a manufacturer-specific family.

Key fields:

- `product_family_id`
- `manufacturer_id`
- `family_code`
- `display_name`
- `source_group_name`
- `normalized_group_name`

### ProductType

Purpose: normalized product type used by Product Selector, catalog filters, Backend Catalog Matcher, UI, and related component rules.

Key fields:

- `product_type_id`
- `product_type_code`
- `display_name`
- `product_kind`
- `manufacturer_scope`
- `filter_profile_id`

Example product types:

- `pressure_gauge`
- `vacuum_gauge`
- `manovacuum_gauge`
- `bimetal_thermometer`
- `thermowell`
- `pressure_transducer`
- `diaphragm_seal`
- `bushing`
- `valve`
- `service_position`

### Series

Purpose: normalized series or model family before concrete SKU selection.

Key fields:

- `series_id`
- `manufacturer_id`
- `product_type_code`
- `series_code`
- `series_name`
- `source_series_name`
- `series_options`
- `supported_services`
- `status`

### CatalogItem

Purpose: normalized catalog item / SKU, separated from stock and analog decisions.

Key fields:

- `catalog_item_id`
- `manufacturer_id`
- `product_type_code`
- `product_kind`
- `series_code`
- `model_code`
- `article`
- `sku`
- `original_name`
- `normalized_name`
- `display_name`
- `search_name`
- `parameters`
- `source_refs`
- `status`

The `parameters` field is conceptually structured by ProductTypeFilterProfile. It is not a universal bag of every possible field.

### CatalogItemParameter

Purpose: machine-readable parameter value attached to a catalog item only when applicable to that product type.

Key fields:

- `catalog_item_id`
- `parameter_code`
- `applicability`
- `value`
- `unit`
- `source_text`
- `normalization_status`
- `confidence`

A missing field is different from `not_applicable`:

- missing required field means parser/import needs review;
- `not_applicable` means the field must not be required or filtered for this product type.

## Parameter Dimensions

Potential parameter dimensions include:

- `measurement_range`
- `range_from`
- `range_to`
- `range_unit`
- `temperature_range`
- `thread`
- `thread_pair`
- `connection`
- `connection_type`
- `process_connection`
- `instrument_connection`
- `accuracy_class`
- `case_diameter`
- `material`
- `material_candidate`
- `membrane_material`
- `execution`
- `options`
- `diameter`
- `stem_diameter`
- `immersion_length`
- `signal_output`
- `pressure_limit`
- `protection_rating`
- `medium`
- `hydrofilling_supported`
- `service_type`
- `quantity_policy`
- `parent_position_ref`
- `compatible_parent_type`
- `compatible_parent_series`
- `compatible_thermowell_rule`
- `assembly_service_required`
- `filling_liquid`
- `fluid_type`

These dimensions become usable filters only through product-type profiles.

## Product Type Filter Profiles

Each `product_type` has its own applicable filter and parameter profile. The profile marks every relevant field as one of:

- `required` - required for reliable matching or import validation for this product type;
- `optional` - can improve matching or filtering when present, but must not block all matching by itself;
- `derived` - calculated or inferred by backend rules from source fields or related rules, not directly required from Product Selector;
- `not_applicable` - must not be used as a UI filter and must not be required from Product Selector or Backend Catalog Matcher for this product type.

Important rule: product-type profiles are mandatory. ArtCRM must not describe all catalog parameters as universal filters for all products.

### Filter Applicability Matrix

| product_type | required | optional | derived | not_applicable |
| --- | --- | --- | --- | --- |
| `pressure_gauge` / манометр | `measurement_range`, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution`, `hydrofilling_supported`, `protection_rating`, `medium` | `range_from`, `range_to`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `vacuum_gauge` / вакуумметр | `measurement_range`, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution` | `range_from`, `range_to`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `manovacuum_gauge` / мановакуумметр | `measurement_range` with negative and positive parts, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution`, `hydrofilling_supported` only for supported series | `range_from`, `range_to`, `range_crosses_zero`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `bimetal_thermometer` / термометр биметаллический | `temperature_range`, `thread`, `immersion_length` | `stem_diameter`, `accuracy_class`, `material`, `execution`, `compatible_thermowell_rule` | `temperature_from`, `temperature_to`, `thermowell_candidate_rule`, `search_name` | pressure `measurement_range`, `hydrofilling_supported`, `signal_output` |
| `thermowell` / гильза | `compatible_parent_type`, `compatible_parent_series`, `immersion_length`, `stem_diameter`, `thread` or `thread_pair` | `material`, `pressure_limit`, `execution` | `compatible_parent_rule`, `search_name` | `measurement_range`, `accuracy_class`, `signal_output`, `hydrofilling_supported` |
| `pressure_transducer` / датчик давления | `measurement_range`, `range_unit`, `thread`, `signal_output`, `accuracy_class` | `material`, `protection_rating`, `execution`, `medium` | `range_from`, `range_to`, `product_kind`, `search_name` | `case_diameter` as gauge case diameter, `immersion_length`, `stem_diameter` |
| `diaphragm_seal` / разделитель сред | `process_connection`, `instrument_connection`, `material` or `material_candidate`, `compatible_parent_type` | `membrane_material`, `pressure_limit`, `medium`, `filling_liquid`, `assembly_service_required` | `compatibility_rule`, `service_requirements`, `search_name` | `accuracy_class` as direct item characteristic, `immersion_length` unless specific subtype requires it, `signal_output` |
| `bushing` / бобышка | `thread`, `compatible_parent_type` | `material`, `execution`, `length`/`size` if present | `compatible_parent_rule`, `search_name` | `measurement_range`, `accuracy_class`, `signal_output`, `hydrofilling_supported` |
| `valve` / кран / клапан | `valve_type`, `thread` or `connection`, `material` or `material_candidate` | `pressure_limit`, `execution` | `connection_normalized`, `search_name` | `measurement_range` as instrument range, `accuracy_class`, `immersion_length`, `signal_output` |
| `service_position` / гидрозаполнение / сборка / заполнение | `service_type`, `parent_position_ref` or `parent_product_type`, `quantity_policy` | `fluid_type`, `parent_case_diameter`, `compatible_parent_series` | `quantity_candidate`, `service_display_name`, `search_name` | `measurement_range` as own range, `thread` as own connection unless service requires it, `accuracy_class` |

### ProductTypeFilterProfile JSON Examples

#### pressure_gauge

```json
{
  "profile_id": "rosma.pressure_gauge.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "pressure_gauge",
  "required": [
    "measurement_range",
    "range_unit",
    "thread",
    "connection_type",
    "accuracy_class"
  ],
  "optional": [
    "case_diameter",
    "material",
    "execution",
    "hydrofilling_supported",
    "protection_rating",
    "medium"
  ],
  "derived": [
    "range_from",
    "range_to",
    "product_kind",
    "search_name"
  ],
  "not_applicable": [
    "immersion_length",
    "stem_diameter",
    "signal_output"
  ],
  "ui_filter_rule": "Do not show not_applicable fields as pressure gauge filters.",
  "matcher_rule": "Do not require signal_output, immersion_length, or stem_diameter for pressure gauges."
}
```

#### bimetal_thermometer

```json
{
  "profile_id": "rosma.bimetal_thermometer.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "bimetal_thermometer",
  "required": [
    "temperature_range",
    "thread",
    "immersion_length"
  ],
  "optional": [
    "stem_diameter",
    "accuracy_class",
    "material",
    "execution",
    "compatible_thermowell_rule"
  ],
  "derived": [
    "temperature_from",
    "temperature_to",
    "thermowell_candidate_rule",
    "search_name"
  ],
  "not_applicable": [
    "measurement_range",
    "hydrofilling_supported",
    "signal_output"
  ],
  "ui_filter_rule": "Use temperature and immersion filters, not pressure range filters.",
  "matcher_rule": "Do not require pressure measurement range or signal_output for bimetal thermometers."
}
```

#### thermowell

```json
{
  "profile_id": "rosma.thermowell.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "thermowell",
  "required": [
    "compatible_parent_type",
    "compatible_parent_series",
    "immersion_length",
    "stem_diameter",
    "thread_or_thread_pair"
  ],
  "optional": [
    "material",
    "pressure_limit",
    "execution"
  ],
  "derived": [
    "compatible_parent_rule",
    "search_name"
  ],
  "not_applicable": [
    "measurement_range",
    "accuracy_class",
    "signal_output",
    "hydrofilling_supported"
  ],
  "ui_filter_rule": "Thermowell filters are compatibility filters, not measuring instrument filters.",
  "matcher_rule": "Do not require accuracy_class for thermowells."
}
```

#### pressure_transducer

```json
{
  "profile_id": "rosma.pressure_transducer.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "pressure_transducer",
  "required": [
    "measurement_range",
    "range_unit",
    "thread",
    "signal_output",
    "accuracy_class"
  ],
  "optional": [
    "material",
    "protection_rating",
    "execution",
    "medium"
  ],
  "derived": [
    "range_from",
    "range_to",
    "product_kind",
    "search_name"
  ],
  "not_applicable": [
    "case_diameter",
    "immersion_length",
    "stem_diameter"
  ],
  "ui_filter_rule": "Show signal_output for pressure transducers; do not show gauge case diameter as a required filter.",
  "matcher_rule": "signal_output is required for pressure transducer matching and not required for pressure gauges."
}
```

#### service_position

```json
{
  "profile_id": "rosma.service_position.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "service_position",
  "required": [
    "service_type",
    "parent_position_ref_or_parent_product_type",
    "quantity_policy"
  ],
  "optional": [
    "fluid_type",
    "parent_case_diameter",
    "compatible_parent_series"
  ],
  "derived": [
    "quantity_candidate",
    "service_display_name",
    "search_name"
  ],
  "not_applicable": [
    "measurement_range",
    "thread",
    "accuracy_class"
  ],
  "ui_filter_rule": "Service positions are filtered by service type and parent compatibility, not by their own measurement range.",
  "matcher_rule": "Do not require measurement_range or accuracy_class for hydrofilling, assembly, or filling service positions."
}
```

## Stock and Availability Layer

Stock and availability must be stored separately from `CatalogItem`.

Purpose:

- keep catalog identity stable even when stock changes;
- support multiple stock sources or dates;
- avoid using stock columns as product identity.

Conceptual fields:

- `stock_record_id`
- `catalog_item_ref`
- `source_file_ref`
- `stock_quantity_candidate`
- `reserved_quantity_candidate`
- `availability_status`
- `stock_date`
- `normalization_status`

## Analog Layer

Analog mappings must be separated from catalog items.

Purpose:

- preserve original item identity;
- record manufacturer-specific analog logic;
- keep manager/backend validation mandatory.

Conceptual fields:

- `analog_rule_id`
- `source_manufacturer`
- `source_product_type`
- `source_model_candidate`
- `target_manufacturer`
- `target_product_type`
- `target_series_candidate`
- `matching_constraints`
- `forbidden_mismatch`
- `validation_required`

## Related Component Rule Layer

Related component rules must be separated from Product Selector suggestions.

Product Selector may output candidate related component suggestions, but backend rule layers decide whether a suggestion is valid, suppressed, or needs review.

Conceptual fields:

- `related_component_rule_id`
- `manufacturer_scope`
- `parent_product_type`
- `parent_series_rule`
- `suggested_product_type`
- `relation_type`
- `required_parent_fields`
- `quantity_policy`
- `duplicate_suppression_key`
- `validation_required`

## Backend Catalog Matcher Boundary

Backend Catalog Matcher is a backend-only service. Conceptually it should:

- accept Product Selector candidate data only after backend validation;
- apply the correct ProductTypeFilterProfile;
- reject filters marked `not_applicable` for the product type;
- preserve missing required fields as `needs_review` instead of inventing values;
- return candidate matches, rejected matches, warnings, and review reasons;
- never calculate prices, VAT, totals, documents, or 1C exchange values unless a later separate task explicitly defines that flow.

The matcher must not call frontend code, expose secrets, or treat LLM output as final business data.

## Deferred Decisions

Deferred to later tasks:

- physical database schema;
- SQL or ORM models;
- import runner implementation;
- catalog parser implementation;
- Backend Catalog Matcher implementation;
- UI filter component implementation;
- loading or committing real Excel files;
- product-owner approved numeric match scoring thresholds.

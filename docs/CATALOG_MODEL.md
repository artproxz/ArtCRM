# Catalog Data Model

This document defines the documentation-only catalog foundation for ArtCRM before catalog import, Backend Catalog Matcher, database schema, or application implementation.

It does not add backend code, frontend code, SQL, ORM, migrations, containers, dependencies, model changes, Ollama calls, fixtures runner, `.env.example` changes, source spreadsheets, secrets, credentials, production emails, or filesystem model paths.

## Purpose

ArtCRM catalog data must not be modeled as a flat SKU list only. The normalized catalog layer must support a constructor-style structure:

1. manufacturer;
2. source hierarchy;
3. product family;
4. product type;
5. product-type-specific filter profile;
6. series/model;
7. concrete catalog item / SKU;
8. stock and availability as a separate layer;
9. analog and related component rules as separate layers.

This structure lets Product Selector candidate data and Backend Catalog Matcher decisions use the correct filters for each product type. A pressure gauge, thermowell, pressure transducer, solenoid valve, relay, thermomanometer, and hydrofilling service-position must not share one universal parameter set.

## Scope

Current manufacturer scope is ROSMA.

Future manufacturers, such as Manotom, Fiztech, WIKA, Kabeltec, and others, must be added through manufacturer-specific mapping profiles and adapters. ROSMA naming, grouping, and matching rules must not become universal rules.

## Source Context

Known source classes for future import:

- ROSMA price/catalog files with item rows and group/header rows;
- stock files with catalog codes, warehouse columns, and expected receipt columns;
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
  -> SourceHierarchy
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
- `thermomanometer` uses both pressure and temperature ranges; it must not be reduced to `pressure_gauge`.
- `solenoid_valve` has valve function and coil/voltage fields; it must not be hidden inside generic `valve` without its own profile.
- `service_position` such as hydrofilling does not have its own measurement range or own thread by default.

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

### SourceHierarchy

Purpose: preserves the source grouping structure from catalog files for audit, normalization, and repeatable parsing.

The file `Все позиции РОСМА.xlsx` contains group/header rows and item rows. Group/header rows are not SKUs. Some product attributes can be derived from the source hierarchy, but those derived attributes must remain traceable.

Key fields:

- `source_hierarchy_path`
- `parent_group_code`
- `parent_group_name`
- `top_group`
- `is_group`
- `is_catalog_item`
- `source_row_kind`
- `source_file_ref`
- `source_sheet_name`
- `source_row_number`

Rules:

- `source_hierarchy_path` must be preserved for audit and repeated normalization.
- `is_group=true` rows are group/header rows and must not be treated as SKU/catalog item rows.
- `is_catalog_item=true` rows can become catalog item candidates after product-type parsing and backend validation.
- `source_row_kind` should distinguish `group_header`, `catalog_item`, `service_position`, `stock_item`, `analog_rule`, and `unknown_or_review_required`.
- Import parser and Backend Catalog Matcher must keep hierarchy references when reporting candidate matches, warnings, and review reasons.

### ProductFamily

Purpose: groups related product types under a manufacturer-specific family.

Key fields:

- `product_family_id`
- `manufacturer_id`
- `family_code`
- `display_name`
- `source_group_name`
- `normalized_group_name`
- `source_hierarchy_path`

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
- `thermomanometer`
- `bimetal_thermometer`
- `thermowell`
- `pressure_transducer`
- `pressure_relay`
- `temperature_relay`
- `diaphragm_seal`
- `bushing`
- `valve`
- `solenoid_valve`
- `service_position`

### ProductKind Vocabulary

Allowed `product_kind` values are controlled:

- `group`
- `main_product`
- `accessory`
- `service_position`
- `spare_part`
- `related_component_candidate`

Do not add `instrument` as a separate product kind. Products that are measuring instruments should normally use `main_product` plus a specific `product_type` such as `pressure_gauge`, `pressure_transducer`, `thermomanometer`, or `bimetal_thermometer`.

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
- `source_hierarchy_path`
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
- `source_hierarchy_path`
- `source_row_kind`
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
- `pressure_range`
- `setpoint_range`
- `range_from`
- `range_to`
- `range_unit`
- `pressure_range_unit`
- `temperature_range`
- `temperature_from`
- `temperature_to`
- `temperature_unit`
- `thread`
- `thread_pair`
- `connection`
- `connection_type`
- `process_connection`
- `instrument_connection`
- `accuracy_class`
- `accuracy_class_pressure`
- `accuracy_class_candidate`
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
- `contact_type`
- `output_type`
- `valve_type`
- `valve_function`
- `voltage_or_coil`
- `port_or_dn_or_thread`
- `pressure_limit`
- `temperature_limit`
- `protection_rating`
- `medium`
- `medium_candidate`
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
- `derived` - calculated or inferred by backend rules from source fields, source hierarchy, or related rules, not directly required from Product Selector;
- `not_applicable` - must not be used as a UI filter and must not be required from Product Selector or Backend Catalog Matcher for this product type.

Important rule: product-type profiles are mandatory. ArtCRM must not describe all catalog parameters as universal filters for all products.

### Filter Applicability Matrix

| product_type | required | optional | derived | not_applicable |
| --- | --- | --- | --- | --- |
| `pressure_gauge` / манометр | `measurement_range`, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution`, `hydrofilling_supported`, `protection_rating`, `medium` | `range_from`, `range_to`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `vacuum_gauge` / вакуумметр | `measurement_range`, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution` | `range_from`, `range_to`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `manovacuum_gauge` / мановакуумметр | `measurement_range` with negative and positive parts, `range_unit`, `thread`, `connection_type`, `accuracy_class` | `case_diameter`, `material`, `execution`, `hydrofilling_supported` only for supported series | `range_from`, `range_to`, `range_crosses_zero`, `product_kind`, `search_name` | `immersion_length`, `stem_diameter`, `signal_output` |
| `thermomanometer` / термоманометр | `pressure_range`, `pressure_range_unit`, `temperature_range`, `temperature_unit`, `thread`, `connection_type`, `accuracy_class_pressure` or `accuracy_class_candidate` | `case_diameter`, `material`, `execution`, `protection_rating`, `medium` | `pressure_range_from`, `pressure_range_to`, `temperature_from`, `temperature_to`, `search_name`, `product_kind` | `signal_output`, `immersion_length` unless a specific thermomanometer subtype requires it |
| `bimetal_thermometer` / термометр биметаллический | `temperature_range`, `thread`, `immersion_length` | `stem_diameter`, `accuracy_class`, `material`, `execution`, `compatible_thermowell_rule` | `temperature_from`, `temperature_to`, `thermowell_candidate_rule`, `search_name` | pressure `measurement_range`, `hydrofilling_supported`, `signal_output` |
| `thermowell` / гильза | `compatible_parent_type`, `compatible_parent_series`, `immersion_length`, `stem_diameter`, `thread` or `thread_pair` | `material`, `pressure_limit`, `execution` | `compatible_parent_rule`, `search_name` | `measurement_range`, `accuracy_class`, `signal_output`, `hydrofilling_supported` |
| `pressure_transducer` / датчик давления | `measurement_range`, `range_unit`, `thread`, `signal_output`, `accuracy_class` | `material`, `protection_rating`, `execution`, `medium` | `range_from`, `range_to`, `product_kind`, `search_name` | `case_diameter` as gauge case diameter, `immersion_length`, `stem_diameter` |
| `pressure_relay` / реле давления | `pressure_range` or `setpoint_range`, `range_unit`, `connection`/`thread`, `contact_type` or `output_type` candidate | `material`, `protection_rating`, `execution`, `medium` | `range_from`, `range_to`, `search_name` | `accuracy_class` as gauge accuracy unless source explicitly provides it, `immersion_length`, `case_diameter` as gauge case diameter |
| `temperature_relay` / реле температуры | `temperature_range` or `setpoint_range`, `temperature_unit`, `sensor`/`probe_type` if present | `connection`/`thread`, `immersion_length` if probe/stem subtype requires it, `contact_type`/`output_type`, `protection_rating`, `execution` | `temperature_from`, `temperature_to`, `search_name` | pressure `measurement_range` unless specific subtype requires it, gauge `accuracy_class`, `case_diameter` as pressure gauge diameter |
| `diaphragm_seal` / разделитель сред | `process_connection`, `instrument_connection`, `material` or `material_candidate`, `compatible_parent_type` | `membrane_material`, `pressure_limit`, `medium`, `filling_liquid`, `assembly_service_required` | `compatibility_rule`, `service_requirements`, `search_name` | `accuracy_class` as direct item characteristic, `immersion_length` unless specific subtype requires it, `signal_output` |
| `bushing` / бобышка | `thread`, `compatible_parent_type` | `material`, `execution`, `length`/`size` if present | `compatible_parent_rule`, `search_name` | `measurement_range`, `accuracy_class`, `signal_output`, `hydrofilling_supported` |
| `valve` / кран / клапан | `valve_type`, `thread` or `connection`, `material` or `material_candidate` | `pressure_limit`, `execution` | `connection_normalized`, `search_name` | `measurement_range` as instrument range, `accuracy_class`, `immersion_length`, `signal_output` |
| `solenoid_valve` / соленоидный клапан | `valve_function`, `voltage_or_coil`, `port_or_dn_or_thread`, `medium` or `medium_candidate` | `pressure_limit`, `material`, `execution`, `protection_rating`, `temperature_limit` | `normalized_connection`, `search_name`, `product_kind` | `measurement_range` as gauge range, `accuracy_class`, `immersion_length`, `signal_output` as sensor output |
| `service_position` / гидрозаполнение / сборка / заполнение | `service_type`, `parent_position_ref` or `parent_product_type`, `quantity_policy` | `fluid_type`, `parent_case_diameter`, `compatible_parent_series` | `quantity_candidate`, `service_display_name`, `search_name` | `measurement_range` as own range, `thread` as own connection by default, `accuracy_class` |

### Special Profile Rules

- `thermomanometer` must not be modeled as a normal `pressure_gauge`, because it has two independent measurement circuits: pressure and temperature.
- `solenoid_valve` must not be hidden in generic `valve` without its own profile, because coil/voltage and function are core matching fields.
- `pressure_relay` and `temperature_relay` may share a future relay family in UI, but their matching fields remain product-type-specific.
- For `service_position`, `thread` is `not_applicable` by default. A concrete service subtype may override this only through a subtype-specific profile. Hydrofilling has no own thread. Assembly or another service may have compatibility fields if the source requires them.

### ProductTypeFilterProfile JSON Examples

#### pressure_gauge

```json
{
  "profile_id": "rosma.pressure_gauge.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "pressure_gauge",
  "required": ["measurement_range", "range_unit", "thread", "connection_type", "accuracy_class"],
  "optional": ["case_diameter", "material", "execution", "hydrofilling_supported", "protection_rating", "medium"],
  "derived": ["range_from", "range_to", "product_kind", "search_name"],
  "not_applicable": ["immersion_length", "stem_diameter", "signal_output"],
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
  "required": ["temperature_range", "thread", "immersion_length"],
  "optional": ["stem_diameter", "accuracy_class", "material", "execution", "compatible_thermowell_rule"],
  "derived": ["temperature_from", "temperature_to", "thermowell_candidate_rule", "search_name"],
  "not_applicable": ["measurement_range", "hydrofilling_supported", "signal_output"],
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
  "required": ["compatible_parent_type", "compatible_parent_series", "immersion_length", "stem_diameter", "thread_or_thread_pair"],
  "optional": ["material", "pressure_limit", "execution"],
  "derived": ["compatible_parent_rule", "search_name"],
  "not_applicable": ["measurement_range", "accuracy_class", "signal_output", "hydrofilling_supported"],
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
  "required": ["measurement_range", "range_unit", "thread", "signal_output", "accuracy_class"],
  "optional": ["material", "protection_rating", "execution", "medium"],
  "derived": ["range_from", "range_to", "product_kind", "search_name"],
  "not_applicable": ["case_diameter", "immersion_length", "stem_diameter"],
  "ui_filter_rule": "Show signal_output for pressure transducers; do not show gauge case diameter as a required filter.",
  "matcher_rule": "signal_output is required for pressure transducer matching and not required for pressure gauges."
}
```

#### thermomanometer

```json
{
  "profile_id": "rosma.thermomanometer.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "thermomanometer",
  "required": ["pressure_range", "pressure_range_unit", "temperature_range", "temperature_unit", "thread", "connection_type", "accuracy_class_pressure"],
  "optional": ["case_diameter", "material", "execution", "protection_rating", "medium"],
  "derived": ["pressure_range_from", "pressure_range_to", "temperature_from", "temperature_to", "search_name", "product_kind"],
  "not_applicable": ["signal_output", "immersion_length"],
  "matcher_rule": "Match pressure and temperature circuits independently; do not collapse thermomanometer into pressure_gauge."
}
```

#### solenoid_valve

```json
{
  "profile_id": "rosma.solenoid_valve.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "solenoid_valve",
  "required": ["valve_function", "voltage_or_coil", "port_or_dn_or_thread", "medium_candidate"],
  "optional": ["pressure_limit", "material", "execution", "protection_rating", "temperature_limit"],
  "derived": ["normalized_connection", "search_name", "product_kind"],
  "not_applicable": ["measurement_range", "accuracy_class", "immersion_length", "signal_output"],
  "matcher_rule": "Do not hide solenoid valves in generic valve profile; coil/voltage is a required matching dimension."
}
```

#### service_position

```json
{
  "profile_id": "rosma.service_position.v1",
  "manufacturer_scope": "ROSMA",
  "product_type": "service_position",
  "required": ["service_type", "parent_position_ref_or_parent_product_type", "quantity_policy"],
  "optional": ["fluid_type", "parent_case_diameter", "compatible_parent_series"],
  "derived": ["quantity_candidate", "service_display_name", "search_name"],
  "not_applicable": ["measurement_range", "thread", "accuracy_class"],
  "subtype_override_rule": "thread is not_applicable by default; a service subtype may override this only through a subtype-specific profile.",
  "matcher_rule": "Do not require measurement_range, own thread, or accuracy_class for hydrofilling, assembly, or filling service positions by default."
}
```

## Stock and Availability Layer

Stock and availability must be stored separately from `CatalogItem`.

Purpose:

- keep catalog identity stable even when stock changes;
- support multiple stock sources, warehouses, and future receipts;
- avoid using stock columns as product identity;
- keep stock data outside Product Selector output.

Conceptual fields:

- `stock_record_id`
- `catalog_item_id`
- `warehouse_code`
- `warehouse_name`
- `available_qty`
- `reserved_qty`
- `expected_receipts[]`
- `expected_receipts[].date`
- `expected_receipts[].qty`
- `expected_receipts[].source_column`
- `stock_updated_at` or `source_effective_date`
- `source_warehouse_column`
- `source_reference`
- `normalization_status`

Rules:

- one catalog item may have multiple stock records;
- multiple stock records may represent different warehouses, dates, or source columns;
- stock records are not part of Product Selector output;
- stock records must not be the only description of a product;
- stock records must reference a catalog item candidate or validated catalog item.

Example StockRecord:

```json
{
  "catalog_item_id": "00000000000",
  "warehouse_code": "rosma_spb",
  "warehouse_name": "Основной склад РОСМА (СПб)",
  "available_qty": 12,
  "reserved_qty": 0,
  "expected_receipts": [
    {
      "date": "2026-05-10",
      "qty": 5,
      "source_column": "expected_receipt_1"
    }
  ],
  "stock_updated_at": "2026-04-27",
  "source_reference": {
    "file_name": "Остатки 27.04.26г.xlsx",
    "source_row": 123
  }
}
```

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
- keep stock and availability separate from identity matching;
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

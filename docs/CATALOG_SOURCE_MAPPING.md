# Catalog Source Mapping

This document defines the documentation-only mapping approach for future ROSMA catalog import and normalization.

It does not add parser code, backend code, frontend code, SQL, ORM, migrations, containers, dependencies, model changes, Ollama calls, fixtures runner, `.env.example` changes, real source spreadsheets, secrets, credentials, production emails, or filesystem model paths.

## Purpose

ArtCRM needs a normalized catalog layer that can be built from messy manufacturer source files while preserving product-type-specific matching rules.

The parser must not apply one universal regex or one universal field list to every source row. It must first identify `product_type` / `product_kind`, then apply the corresponding parsing and filter profile.

## Source Types

Future import may use these source classes:

- ROSMA catalog / price files;
- ROSMA stock / availability files;
- analog tables;
- naming and rule references;
- related component rule references.

Uploaded Excel source files are reference inputs only. They must not be committed as part of this documentation task.

## Source Row Classification

Before field extraction, the parser should classify each source row.

Conceptual row classes:

- `group_header` - group or section heading, not a catalog item;
- `catalog_item` - concrete sellable SKU/catalog row;
- `service_position` - service row such as hydrofilling, assembly, filling;
- `stock_item` - stock or availability row referencing a catalog code;
- `analog_rule` - analog mapping row;
- `unknown_or_review_required` - row that cannot be safely classified.

Conceptual classification fields:

- `source_file_ref`
- `source_sheet_name`
- `source_row_number`
- `raw_name`
- `raw_code`
- `raw_group_path`
- `source_hierarchy_path`
- `parent_group_code`
- `parent_group_name`
- `top_group`
- `is_group`
- `is_catalog_item`
- `source_row_kind`
- `row_class`
- `manufacturer_candidate`
- `product_family_candidate`
- `product_type_candidate`
- `product_kind_candidate`
- `classification_confidence`
- `classification_warnings`

Group/header rows from `Все позиции РОСМА.xlsx` are not SKUs. The parser must preserve `source_hierarchy_path` because some product attributes can be derived from group context and because audit/re-normalization depends on the original hierarchy.

## ProductKind Vocabulary

Allowed `product_kind` values are:

- `group`
- `main_product`
- `accessory`
- `service_position`
- `spare_part`
- `related_component_candidate`

Do not use `instrument` as a separate `product_kind`. Measuring instruments are represented as `product_kind=main_product` with a specific `product_type` such as `pressure_gauge`, `pressure_transducer`, `thermomanometer`, or `bimetal_thermometer`.

## Product-Type-Specific Parsing Profiles

The parser must apply different parsing profiles by `product_type`. The pipeline should be:

1. normalize source text for safe parsing;
2. classify row as group, item, service, stock, analog, or unknown;
3. preserve normalized source hierarchy fields;
4. determine manufacturer scope;
5. determine product family;
6. determine `product_type` and `product_kind`;
7. load the matching ProductTypeFilterProfile from [Catalog Data Model](CATALOG_MODEL.md);
8. extract only fields that are required, optional, or derived for that product type;
9. mark missing required fields as review issues;
10. ignore or reject fields that are `not_applicable` for that product type;
11. emit normalized candidate records for backend validation.

Important examples:

- `pressure_gauge` may parse pressure `measurement_range`, `range_unit`, `thread`, `connection_type`, and `accuracy_class`; it must not require `immersion_length` or `signal_output`.
- `bimetal_thermometer` may parse `temperature_range`, `thread`, and `immersion_length`; it must not use pressure `measurement_range` or `hydrofilling_supported` as direct filters.
- `thermowell` must parse compatibility fields such as `compatible_parent_series`, `immersion_length`, `stem_diameter`, and `thread` or `thread_pair`; it must not require `accuracy_class`.
- `pressure_transducer` must parse `signal_output`; a pressure gauge must not require `signal_output`.
- `thermomanometer` must parse both pressure and temperature ranges; it must not be treated as a normal pressure gauge.
- `solenoid_valve` must parse valve function, coil/voltage, port/DN/thread, and medium; it must not be hidden in generic valve parsing.
- `service_position` such as hydrofilling must parse `service_type`, parent reference/type, and `quantity_policy`; it must not require its own measurement range or own thread by default.

## Mapping Profiles

### pressure_gauge

Parsing profile should extract:

- `series_code`
- `model_code`
- `measurement_range`
- `range_from`
- `range_to`
- `range_unit`
- `thread`
- `connection_type`
- `accuracy_class`
- optional `case_diameter`
- optional `material`
- optional `execution`
- optional `hydrofilling_supported`
- optional `protection_rating`
- optional `medium`

Must not extract as required filters:

- `immersion_length`
- `stem_diameter`
- `signal_output`

### vacuum_gauge

Parsing profile should extract:

- `series_code`
- `model_code`
- negative vacuum `measurement_range`
- `range_from`
- `range_to`
- `range_unit`
- `thread`
- `connection_type`
- `accuracy_class`
- optional `case_diameter`
- optional `material`
- optional `execution`

Must not extract as required filters:

- `immersion_length`
- `stem_diameter`
- `signal_output`

### manovacuum_gauge

Parsing profile should extract:

- `series_code`
- `model_code`
- measurement range with negative and positive parts;
- `range_from`
- `range_to`
- `range_unit`
- `thread`
- `connection_type`
- `accuracy_class`
- optional `case_diameter`
- optional `material`
- optional `execution`
- optional `hydrofilling_supported` only when the series supports it

Must not extract as required filters:

- `immersion_length`
- `stem_diameter`
- `signal_output`

### thermomanometer

Parsing profile should extract two independent measurement circuits:

- `series_code`
- `model_code`
- `pressure_range`
- `pressure_range_from`
- `pressure_range_to`
- `pressure_range_unit`
- `temperature_range`
- `temperature_from`
- `temperature_to`
- `temperature_unit`
- `thread`
- `connection_type`
- `accuracy_class_pressure` or `accuracy_class_candidate`
- optional `case_diameter`
- optional `material`
- optional `execution`
- optional `protection_rating`
- optional `medium`

Must not extract as required filters:

- `signal_output`
- `immersion_length` unless a specific thermomanometer subtype requires it

Thermomanometers must not be normalized as plain `pressure_gauge` rows because pressure and temperature ranges are independent matching dimensions.

### bimetal_thermometer

Parsing profile should extract:

- `series_code`
- `model_code`
- `temperature_range`
- `temperature_from`
- `temperature_to`
- `thread`
- `immersion_length`
- optional `stem_diameter`
- optional `accuracy_class`
- optional `material`
- optional `execution`
- optional `compatible_thermowell_rule`

Must not extract as required filters:

- pressure `measurement_range`
- `hydrofilling_supported`
- `signal_output`

If `immersion_length` is missing and a thermowell needs to be suggested or matched, the record must go to review.

### thermowell

Parsing profile should extract:

- `compatible_parent_type`
- `compatible_parent_series`
- `immersion_length`
- `stem_diameter`
- `thread` or `thread_pair`
- optional `material`
- optional `pressure_limit`
- optional `execution`

Must not extract as required filters:

- `measurement_range`
- `accuracy_class`
- `signal_output`
- `hydrofilling_supported`

Thread rule examples:

- for series `211`, source may include outer thread such as `G1/2` or `M20x1,5`;
- for series `220`, source may include a thread pair such as `G1/2-G1/2`.

### pressure_transducer

Parsing profile should extract:

- `series_code`
- `model_code`
- `measurement_range`
- `range_from`
- `range_to`
- `range_unit`
- `thread`
- `signal_output`
- `accuracy_class`
- optional `material`
- optional `protection_rating`
- optional `execution`
- optional `medium`

Must not extract as required filters:

- `case_diameter` as gauge case diameter;
- `immersion_length`;
- `stem_diameter`.

### pressure_relay

Parsing profile should extract:

- `series_code`
- `model_code`
- `pressure_range` or `setpoint_range`
- `range_from`
- `range_to`
- `range_unit`
- `connection` or `thread`
- `contact_type` or `output_type` candidate
- optional `material`
- optional `protection_rating`
- optional `execution`
- optional `medium`

Must not extract as required filters:

- gauge `accuracy_class` unless source explicitly provides it;
- `immersion_length`;
- `case_diameter` as gauge case diameter.

### temperature_relay

Parsing profile should extract:

- `series_code`
- `model_code`
- `temperature_range` or `setpoint_range`
- `temperature_from`
- `temperature_to`
- `temperature_unit`
- `sensor_type` or `probe_type` if present
- optional `connection` or `thread`
- optional `immersion_length` if probe/stem subtype requires it
- optional `contact_type` or `output_type`
- optional `protection_rating`
- optional `execution`

Must not extract as required filters:

- pressure `measurement_range` unless a specific subtype requires it;
- gauge `accuracy_class`;
- `case_diameter` as pressure gauge diameter.

### diaphragm_seal

Parsing profile should extract:

- `process_connection`
- `instrument_connection`
- `material` or `material_candidate`
- `compatible_parent_type`
- optional `membrane_material`
- optional `pressure_limit`
- optional `medium`
- optional `filling_liquid`
- optional `assembly_service_required`

Must not extract as required filters:

- `accuracy_class` as direct item characteristic;
- `immersion_length` unless a specific subtype explicitly requires it;
- `signal_output`.

### bushing

Parsing profile should extract:

- `thread`
- `compatible_parent_type`
- optional `material`
- optional `execution`
- optional `length` / `size` when present

Must not extract as required filters:

- `measurement_range`
- `accuracy_class`
- `signal_output`
- `hydrofilling_supported`

### valve

Parsing profile should extract:

- `valve_type`
- `thread` or `connection`
- `material` or `material_candidate`
- optional `pressure_limit`
- optional `execution`

Must not extract as required filters:

- `measurement_range` as instrument range;
- `accuracy_class`;
- `immersion_length`;
- `signal_output`.

### solenoid_valve

Parsing profile should extract:

- `valve_function`
- `voltage_or_coil`
- `port_or_dn_or_thread`
- `medium` or `medium_candidate`
- optional `pressure_limit`
- optional `material`
- optional `execution`
- optional `protection_rating`
- optional `temperature_limit`

Derived fields:

- `normalized_connection`
- `search_name`
- `product_kind`

Must not extract as required filters:

- `measurement_range` as gauge range;
- `accuracy_class`;
- `immersion_length`;
- `signal_output` as sensor output.

Solenoid valves must not be normalized as generic `valve` rows without preserving `product_type=solenoid_valve`.

### service_position

Parsing profile should extract:

- `service_type`
- `parent_position_ref` or `parent_product_type`
- `quantity_policy`
- optional `fluid_type`
- optional `parent_case_diameter`
- optional `compatible_parent_series`

Must not extract as required filters by default:

- `measurement_range` as own range;
- `thread` as own connection;
- `accuracy_class`.

Service-position thread rule:

- `thread` is `not_applicable` by default for `service_position`;
- a concrete service subtype may override this only through a subtype-specific profile;
- hydrofilling has no own thread;
- assembly or another service may have compatibility fields if required by the source.

Hydrofilling examples:

- `Гидрозаполнение глицерином для манометра диам.100` maps to `service_type=hydrofilling`, `fluid_type=glycerin`, `parent_case_diameter=100`.
- `Гидрозаполнение силиконом для манометра диам.100` maps to `service_type=hydrofilling`, `fluid_type=silicone`, `parent_case_diameter=100`.
- Missing fluid type must produce review question: `Уточнить тип гидрозаполнения: глицерин или силикон?`.

## Raw Source Record DTO

```json
{
  "source_file_ref": "source-file-ref",
  "source_sheet_name": "catalog",
  "source_row_number": 123,
  "raw_code": "source-code-candidate",
  "raw_name": "source item name",
  "raw_group_path": ["manufacturer group", "product family group"],
  "source_hierarchy_path": ["top group", "child group"],
  "parent_group_code": "group-code-candidate",
  "parent_group_name": "parent group name",
  "top_group": "top group name",
  "is_group": false,
  "is_catalog_item": true,
  "source_row_kind": "catalog_item",
  "raw_columns": {
    "demo_column": "demo value"
  },
  "row_class": "catalog_item",
  "classification_status": "candidate"
}
```

## Normalized Catalog Candidate DTO

```json
{
  "manufacturer": "ROSMA",
  "product_family": "pressure instruments",
  "product_type": "pressure_gauge",
  "product_kind": "main_product",
  "series_code": "521",
  "model_code": "ТМ-521Р",
  "article": "candidate-article",
  "sku": "candidate-sku",
  "original_name": "source item name",
  "normalized_name": "normalized item name",
  "display_name": "display item name",
  "search_name": "search optimized item name",
  "source_hierarchy_path": ["Манометры", "ТМ-521"],
  "source_row_kind": "catalog_item",
  "filter_profile_id": "rosma.pressure_gauge.v1",
  "parameters": {
    "measurement_range": "0-1MPa",
    "range_unit": "MPa",
    "thread": "G1/2",
    "connection_type": "radial",
    "accuracy_class": "1,0",
    "case_diameter": 100,
    "hydrofilling_supported": true
  },
  "not_applicable_parameters": [
    "immersion_length",
    "stem_diameter",
    "signal_output"
  ],
  "normalization_status": "candidate",
  "validation_required": true
}
```

## Stock Mapping

Stock rows should map to a separate stock/availability candidate, not mutate catalog identity.

Stock mapping must support multi-warehouse values and expected future receipts from stock source columns.

Conceptual fields:

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

Rules:

- one catalog item can have multiple stock records;
- stock records are not part of Product Selector output;
- stock records must not be the only product description;
- stock records must reference catalog identity through `catalog_item_id` or a validated catalog item candidate.

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
  "source_warehouse_column": "warehouse_spb_available",
  "source_reference": {
    "file_name": "Остатки 27.04.26г.xlsx",
    "source_row": 123
  }
}
```

## Analog Mapping

Analog rows should map to analog candidates, separated from catalog item identity.

```json
{
  "source_manufacturer": "future-source-manufacturer",
  "source_product_type": "pressure_gauge",
  "source_model_candidate": "source-model-candidate",
  "target_manufacturer": "ROSMA",
  "target_product_type": "pressure_gauge",
  "target_series_candidate": "target-series-candidate",
  "matching_constraints": ["range", "thread", "accuracy_class"],
  "forbidden_mismatch": ["wrong_range", "wrong_thread"],
  "validation_required": true
}
```

## Related Component Rule Mapping

Related component rule rows or references should map to rules, not to confirmed Product Selector suggestions.

```json
{
  "manufacturer_scope": "ROSMA",
  "parent_product_type": "pressure_gauge",
  "parent_series_rule": "hydrofilling_supported_series_only",
  "suggested_product_type": "service_position",
  "relation_type": "hydrofilling",
  "required_parent_fields": ["series", "case_diameter", "quantity"],
  "quantity_policy": "same_as_parent",
  "duplicate_suppression_key": "parent_position_ref+service_type+fluid_type",
  "validation_required": true
}
```

## Validation and Review Rules

A parsed catalog candidate needs review when:

- row class is unknown;
- product type is uncertain;
- a required field in the product-type profile is missing;
- a field appears that is `not_applicable` for the product type and affects matching;
- a source row mixes multiple product types;
- a service row lacks parent compatibility data;
- a stock row cannot be connected to a catalog item candidate;
- an analog row lacks source or target constraints;
- parser confidence is low.

Review should preserve the raw source reference and normalized candidate data. It must not invent missing values.

## Backend Catalog Matcher Input Boundary

Future Backend Catalog Matcher should consume only backend-validated catalog candidates and Product Selector candidate data.

Matcher input should include:

- `product_type`
- `product_kind`
- `filter_profile_id`
- candidate required fields for that product type;
- optional fields when available;
- explicitly absent or not applicable fields;
- `must_have[]`
- `forbidden_mismatch[]`
- source refs and validation status.

The matcher must reject attempts to use `not_applicable` fields as required filters. For example:

- do not require `immersion_length` for `pressure_gauge`;
- do not require `accuracy_class` for `thermowell`;
- do not require `measurement_range` or own `thread` for `service_position` by default;
- do require `signal_output` for `pressure_transducer`, but do not require it for `pressure_gauge`;
- do not collapse `thermomanometer` into `pressure_gauge`;
- do not collapse `solenoid_valve` into generic `valve`.

## Deferred Implementation

Deferred to later tasks:

- Excel parsing code;
- import runners;
- database schema;
- SQL/ORM/migrations;
- backend API endpoints;
- UI filters;
- automated quality checks;
- loading real catalog or stock files into runtime storage.

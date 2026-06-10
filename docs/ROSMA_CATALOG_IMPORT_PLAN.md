# ROSMA Catalog Import Plan

This document defines the documentation-only plan for future ROSMA catalog, stock, price, analog, and related-component source imports in ArtCRM.

It does not add parser code, backend code, frontend code, SQL, ORM, migrations, PostgreSQL or Redis setup, dependencies, containers, Ollama calls, model or Modelfile changes, `.env.example` changes, source spreadsheets, real catalog rows, real stock rows, real prices, customer data, production emails, credentials, tokens, secrets, private keys, or filesystem model paths.

## Purpose

ArtCRM needs a repeatable import process so catalog matching can work against normalized, reviewed, and versioned data instead of raw spreadsheets.

The catalog and stock layers have different responsibilities:

- Catalog data defines stable product identity: manufacturer, source hierarchy, product type, product kind, series/model, SKU/code, and normalized product parameters.
- Stock data defines changing availability: warehouse quantity, reserves, expected receipts, stock date, and source reference.
- Catalog identity may change rarely, while stock and availability may change daily.
- Stock records must reference catalog identity; they must not become the only description of a product.

ROSMA has a special import mode because it is the primary manufacturer/supplier in the current ArtCRM scope and has both a catalog source and a daily stock/availability file. For MVP, the daily stock file may be uploaded manually. Later, the same data model can support scheduled or API-based import.

Other manufacturers may start in catalog-only mode. Their catalog items can exist in the normalized catalog without daily stock records, and availability can remain `unknown`, `manual`, or `quote_based`. ArtCRM must not require a stock feed from every manufacturer.

## Source Files

Uploaded source files are reference inputs for future import only. They must not be committed to the repository, and this document intentionally does not include real catalog rows, real stock rows, real prices, or customer data.

### ROSMA Catalog Source

Example source file: `Все позиции РОСМА.xlsx`.

Purpose:

- create or update ROSMA catalog item identity;
- preserve ROSMA source hierarchy;
- separate group/header rows from item/SKU rows;
- support constructor-style parsing through product-type-specific profiles from `docs/CATALOG_MODEL.md`.

Conceptual source content:

- group/header rows that describe catalog sections and hierarchy;
- item/SKU rows that represent concrete sellable products or service positions;
- source codes or catalog codes;
- raw names and descriptions;
- source hierarchy/group context;
- product family/type hints;
- series/model hints;
- product parameters embedded in names or columns;
- optional price-related source columns if present in the catalog/price source.

Catalog/price source data must be normalized into catalog candidates before publication. Price columns, if imported later, must be handled as source attributes or a dedicated pricing layer and must not replace catalog identity validation.

### ROSMA Stock Source

Example source file: `Остатки 27.04.26г.xlsx`.

Purpose:

- update stock records for existing catalog items;
- support multiple warehouses;
- track available quantity, reserved quantity, and future receipts;
- publish the latest stock snapshot for Backend Catalog Matcher;
- keep stock history/audit.

Conceptual source content:

- catalog code or source code used to match a catalog item;
- warehouse code or warehouse name;
- available quantity;
- reserved quantity;
- expected receipt date and quantity;
- stock file date or source effective date;
- source reference, sheet name, row number, and file metadata.

The ROSMA stock source may be uploaded daily. Manual upload is acceptable for MVP, while scheduled import can be added later without changing the conceptual model.

### Analog Source

Future analog sources may contain mapping rules between requested products and acceptable alternatives.

Rules:

- analog data must not be mixed with catalog item identity;
- analog data should reference normalized catalog items or source codes when possible;
- analog suggestions require backend validation and review rules before they influence matching decisions;
- analog import must keep source metadata and versioning separate from catalog publication.

### Related Component Source Or Rules

Future related-component sources or rules may describe recommended accessories, services, and compatibility relationships.

Rules:

- related component rules must not be mixed with Product Selector suggestions;
- Product Selector may output candidate suggestions, but source/rule imports define reviewed backend knowledge;
- related component records must preserve parent compatibility, manufacturer scope, quantity policy, and validation status;
- related component publication must be reviewable and versioned.

## Import Flows

### Flow A: ROSMA Catalog Import

1. Upload source file.
2. Register source metadata.
3. Read sheets and rows.
4. Classify rows:
   - `group_header`;
   - `catalog_item`;
   - `service_position`;
   - `unknown_or_review_required`.
5. Preserve `source_hierarchy_path`.
6. Determine `manufacturer = ROSMA`.
7. Determine `product_family`, `product_type`, and `product_kind`.
8. Apply the product-type-specific parsing profile from `docs/CATALOG_MODEL.md`.
9. Build a normalized catalog candidate.
10. Validate required, optional, derived, and `not_applicable` fields.
11. Detect duplicates and conflicts.
12. Build import diff:
    - new item;
    - changed item;
    - unchanged item;
    - deprecated or missing item;
    - review required.
13. Send candidate changes to manager/catalog admin review.
14. Approve reviewed changes.
15. Publish to the active catalog.
16. Archive the previous source version.

Important rules:

- group/header rows are not SKU rows;
- the import process must preserve group hierarchy for audit and future renormalization;
- product-type-specific profiles must decide which fields are required, optional, derived, or not applicable;
- catalog import may create or update catalog identity after validation and approval;
- raw Excel rows must not be used directly by Backend Catalog Matcher.

### Flow B: ROSMA Daily Stock Import

1. Upload stock file manually for MVP.
2. Register source metadata.
3. Read stock rows.
4. Match each row to a catalog item by source code or catalog code.
5. Create or update stock records.
6. Support multiple warehouses.
7. Support `available_qty`, `reserved_qty`, and `expected_receipts[]`.
8. Mark `stock_updated_at` or `source_effective_date`.
9. Produce stock diff:
   - quantity changed;
   - new stock record;
   - item not found in catalog;
   - item disappeared from stock file;
   - future receipt changed.
10. Publish stock update.
11. Keep stock history and audit trail.

Important rules:

- stock import must not create product identity by itself;
- stock import may create `unresolved_stock_item` if `catalog_item_id` is missing;
- unresolved stock rows require review;
- stock data must not be Product Selector output;
- one catalog item may have multiple stock records, for example one per warehouse;
- future receipts must stay tied to the stock source and publication snapshot.

### Flow C: Non-ROSMA Catalog-Only Import

Other manufacturers may have catalog sources without stock sources.

Rules:

- catalog items can exist with `availability_status=unknown`, `manual`, or `quote_based`;
- no daily stock import is required for non-ROSMA manufacturers;
- Backend Catalog Matcher may still match catalog items, but availability remains unknown until manually provided, requested from supplier, or imported through a future manufacturer-specific stock source;
- manufacturer-specific adapters must not assume ROSMA file layout, daily stock availability, or ROSMA naming rules.

### Analog And Related Component Import Strategy

Analog and related-component data should be imported through separate source types and publication flows.

Rules:

- analog import may create candidate analog relationships, not catalog identity;
- related-component import may create candidate compatibility or recommendation rules, not Product Selector output;
- both source classes require validation, diff, review, approval, publication, and versioning;
- both source classes must preserve source metadata for audit.

## Source Metadata

Every uploaded source should register metadata before parsing.

Conceptual fields:

- `source_id`;
- `source_type`: `catalog`, `stock`, `analog`, or `related_component_rules`;
- `manufacturer`;
- `uploaded_at`;
- `uploaded_by`;
- `file_name`;
- `file_hash`;
- `sheet_name`;
- `parser_profile_version`;
- `source_effective_date`;
- `import_mode`: `manual`, `scheduled`, or `API`;
- `status`: `uploaded`, `parsed`, `normalized`, `validated`, `review_required`, `approved`, `published`, `rejected`, or `archived`.

Metadata rules:

- `file_hash` is required for duplicate upload detection and audit;
- `source_effective_date` is required for stock snapshot freshness checks;
- `parser_profile_version` is required so old imports can be explained after parsing rules change;
- source metadata must be stored without exposing secrets or local filesystem paths.

## Catalog Candidate Model

Catalog import builds candidate records before publication.

Conceptual fields:

- raw source reference;
- source hierarchy;
- source row classification;
- manufacturer;
- product family;
- product type;
- product kind;
- series/model;
- source code or catalog code;
- normalized name;
- parameter values;
- normalization status;
- validation warnings;
- required missing fields;
- `not_applicable` violations;
- duplicate/conflict markers;
- confidence.

Rules:

- catalog candidates are not active catalog items until approved and published;
- group/header rows may produce hierarchy records, but must not be published as SKU items;
- service positions require compatibility rules when they depend on a parent product;
- product-type profiles from `docs/CATALOG_MODEL.md` determine required, optional, derived, and not-applicable fields.

## Stock Candidate Model

Stock import builds stock candidates before publication.

Conceptual fields:

- source code;
- matched `catalog_item_id`;
- `warehouse_code`;
- `warehouse_name`;
- `available_qty`;
- `reserved_qty`;
- `expected_receipts[]`;
- `stock_updated_at`;
- `source_reference`;
- `match_status`: `matched`, `unmatched`, `ambiguous`, or `review_required`.

Rules:

- stock candidates must reference catalog identity when matched;
- unmatched rows stay unresolved until reviewed;
- stock candidates do not define manufacturer, product type, series, or normalized product parameters by themselves;
- stock candidates are not Product Selector outputs.

## Validation Errors

Validation errors must be explicit and reviewable. Error summaries must not include secrets, full file paths, production emails, credentials, or sensitive customer data.

Catalog import errors:

- unknown `product_type`;
- unknown `product_kind`;
- group row detected as SKU;
- missing required field for product type;
- invalid range;
- invalid unit;
- invalid thread;
- invalid accuracy class;
- `not_applicable` field used as required;
- duplicate `normalized_name`;
- duplicate `source_code`;
- conflicting source hierarchy;
- service position without parent compatibility;
- hydrofilling attached to unsupported series;
- thermowell without `L` or `d`;
- thermomanometer missing pressure or temperature circuit.

Stock import errors:

- stock row without catalog code;
- stock row catalog code not found;
- duplicate stock row for same warehouse/item;
- invalid quantity;
- negative `available_qty` unless explicitly allowed as correction;
- expected receipt without date;
- expected receipt without quantity;
- unknown warehouse;
- stock file date missing;
- stock source older than current published stock.

## Diff And Review

Catalog and stock imports must produce reviewable diffs before publication.

Catalog diff should identify:

- new catalog item;
- changed catalog item;
- unchanged catalog item;
- deprecated or missing item;
- duplicate/conflict;
- review required.

Stock diff should identify:

- quantity changed;
- new warehouse stock record;
- stock row matched to existing item;
- stock row unmatched to catalog;
- item disappeared from current stock file;
- future receipt changed;
- stale source rejected.

Review rules:

- manager/catalog admin approval is required before publishing catalog changes;
- stock import can have a faster approval path, but unresolved/ambiguous rows still require review;
- review queue must preserve source metadata, candidate data, validation errors, warnings, and diff status;
- publication must be reversible by source version or snapshot version.

Rollback rules:

- catalog rollback restores the previous catalog publication version;
- stock rollback can revert a stock import by `source_id` or published stock snapshot;
- rollback must not delete source metadata or audit history.

## Versioning

Catalog and stock versioning must be separate.

Conceptual versions:

- `catalog_source_version`: one uploaded and parsed catalog source version;
- `catalog_publication_version`: one approved active catalog publication;
- `stock_source_version`: one uploaded and parsed stock source version;
- `stock_snapshot_version`: one published availability snapshot.

Rules:

- catalog source may be updated rarely;
- stock source may be updated daily;
- publication version should point to source version and parser profile version;
- Backend Catalog Matcher should use active catalog publication plus latest relevant published stock snapshot.

## Audit And History

Future implementation must keep enough audit data to explain a match, import decision, or stock answer later.

Audit fields should include:

- source file metadata;
- source row reference;
- parser profile version;
- normalized candidate data;
- validation result;
- diff result;
- reviewer/approver identity;
- publication timestamp;
- rollback events if any.

Audit records must not store real secrets, local filesystem model paths, private keys, or full sensitive prompts.

## Relationship To Backend Catalog Matcher

Backend Catalog Matcher uses published, validated data only.

Rules:

- matcher uses the active catalog version;
- matcher reads the latest published stock snapshot for ROSMA;
- for non-ROSMA manufacturers, availability can be `unknown`, `manual`, or `quote_based`;
- matcher must not depend on Product Selector for stock;
- matcher must not trust raw Excel directly;
- matcher must treat unresolved stock rows as unavailable for automatic availability decisions until reviewed;
- matcher can use source hierarchy and product-type-specific profiles for explainability and filtering.

## Relationship To Product Selector

Product Selector and source import have different responsibilities.

Rules:

- Product Selector only outputs structured intent and candidate data;
- Product Selector does not import catalog;
- Product Selector does not import stock;
- Product Selector does not decide exact availability;
- Product Selector does not approve catalog items, stock records, prices, or related-component rules;
- Product Selector output is checked later by Backend Catalog Matcher against active catalog and stock snapshots.

## MVP Manual Upload

For MVP, ROSMA daily stock import may be manual.

Rules:

- the future admin/import interface can accept a manually uploaded ROSMA stock file;
- no automated scheduler is required yet;
- uploaded file must still go through source registration, validation, diff, and publish;
- manual upload must keep stock history and source audit;
- later automation may replace manual upload without changing the data model.

## Deferred Decisions

Deferred implementation decisions:

- exact parser implementation and libraries;
- exact database schema and migration plan;
- exact admin/import UI screens;
- scheduled import mechanism;
- warehouse master-data source;
- price layer ownership and approval policy;
- analog import source format;
- related-component source format;
- retention policy for archived source files and snapshots.
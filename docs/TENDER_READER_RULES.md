# Tender Reader Rules

This document defines the documentation-only architecture for Tender Reader mode in ArtCRM. Tender Reader is an MVP mode/subtype of Mail Reader Agent for tender notification emails. It extracts candidate tender metadata and candidate tender relevance classification for backend/rules/manager review.

It does not implement email connector, mailbox folder integration, tender-site scraping, browser automation, backend jobs, cron/scheduler, parser code, API endpoints, database schema, SQL, ORM, migrations, UI, pricing logic, commercial offer generation, invoice generation, PDF generation, 1C flow, bid submission, tender platform integration, dependencies, containers, Ollama/model changes, `.env.example` changes, credentials, secrets, real tender emails, or real customer data.

## Purpose

Tender Reader helps a manager quickly understand whether a tender notification is worth reviewing.

Tender Reader does not:

- submit bids;
- generate commercial offers / КП;
- calculate prices;
- calculate VAT, totals, margin, or delivery;
- confirm stock or availability;
- guarantee that a tender is relevant;
- confirm SKU/catalog item;
- scrape tender platforms;
- download tender documents;
- own the final keep/skip/escalate decision.

Tender Reader only extracts structured candidate metadata and candidate classification. Final decision belongs to backend rules and manager review.

This follows the ArtCRM Agent Platform rule: LLM agents extract, structure, explain, and draft; backend services and managers own validated business decisions.

## Scope

Covered here:

- Tender Reader mode as subtype/mode of Mail Reader Agent;
- future Tender Monitor Agent boundary;
- tender folder input boundary;
- tender email metadata extraction;
- tender classification taxonomy;
- configurable filters;
- versioned filter rules;
- product/category matching;
- manufacturer/supplier hints;
- `keep`, `skip`, `needs_review`, and `blocked_irrelevant` candidate decisions;
- manual review workflow;
- audit fields;
- deadline urgency;
- relationship to staff workspace, notifications/SLA, analytics, commercial offer, supplier quote workflow, and document center;
- strict no-implementation boundary.

Not covered here:

- email connector implementation;
- mailbox folder integration;
- tender-site scraping;
- backend jobs;
- cron/scheduler;
- parser code;
- API endpoints;
- database schema;
- migrations;
- UI;
- pricing;
- КП/PDF/invoice/1C generation;
- bid submission;
- tender platform integration;
- dependencies;
- containers;
- model changes.

## Readiness Status

Tender Reader mode is target/documented only. It is not implemented in this task.

For MVP, Tender Reader can be documented as a mode/subtype of Mail Reader Agent because both process email content and produce candidate structured data. If tender volume, rules, deadlines, or platform integrations grow, this mode may evolve into a separate Tender Monitor Agent later.

## Tender Folder Input Boundary

Future input source is a dedicated tender email folder, mailbox label, or controlled backend ingestion source.

Rules:

- Tender Reader reads only controlled input passed by backend/orchestrator;
- no direct mailbox access in this task;
- no Gmail, IMAP, Exchange, or other mail integration in this task;
- no external tender website scraping;
- no browser automation;
- no platform crawling;
- no automatic download of tender documents;
- attachment contents are not parsed automatically;
- the backend/orchestrator is responsible for selecting safe input and excluding secrets/credentials.

Conceptual input fields:

- `source_email_ref`;
- `mailbox_folder_ref`;
- `received_at`;
- `subject`;
- `sender`;
- `body_text`;
- `attachments_metadata`;
- `source_headers`;
- `ingestion_context`.

Input data may include buyer/customer information and must be handled under privacy and security rules. Documentation examples must not contain real tender emails or real customer data.

## Tender Metadata Extraction

Tender Reader extracts candidate metadata only. Backend validation and manager review decide final business meaning.

Conceptual extracted fields:

- `tender_id_candidate`;
- `tender_url_candidate`;
- `tender_platform`;
- `platform_name`;
- `platform_notice_number`;
- `buyer_name`;
- `buyer_inn_candidate`;
- `procurement_region`;
- `delivery_region`;
- `deadline_at`;
- `publication_date`;
- `application_start_date`;
- `application_end_date`;
- `auction_date`;
- `contract_start_date`;
- `contract_end_date`;
- `estimated_value_candidate`;
- `currency_candidate`;
- `product_keywords`;
- `manufacturer_hints`;
- `category_hints`;
- `quantity_hints`;
- `technical_requirement_hints`;
- `attachment_hints`;
- `matched_supported_categories`;
- `matched_unsupported_categories`;
- `matched_manufacturer_focus`;
- `missing_fields`;
- `ambiguity_flags`;
- `source_fragments`;
- `confidence`.

Extraction rules:

- URLs, IDs, dates, buyer names, and manufacturer/category hints are candidates;
- extracted values must preserve source fragments for manager review;
- missing or conflicting critical metadata should drive `needs_review`;
- estimated value is candidate only and not a commercial calculation;
- no real tender or buyer data should be embedded in docs.

## Initial Product Focus

Initial tender relevance focuses on КИП / instrumentation categories Artmatika may supply.

Supported focus examples:

- КИП;
- measuring instruments;
- pressure gauges;
- vacuum gauges;
- manovacuum gauges;
- low pressure gauges;
- bimetal thermometers;
- thermomanometers;
- pressure sensors / transducers;
- pressure relays;
- temperature relays;
- valves;
- solenoid valves;
- thermowells;
- diaphragm seals;
- adapters;
- siphon tubes;
- instrumentation accessories;
- hydrofilling as related/service signal;
- ROSMA;
- Fiztech;
- Manotom;
- similar instrumentation manufacturers and categories.

Tenders outside supplied scope should be classified as `skip` or `blocked_irrelevant` depending on certainty and configured rules.

## Supported And Unsupported Product Categories

Supported category examples:

- pressure gauges;
- vacuum gauges;
- manovacuum gauges;
- low pressure gauges;
- bimetal thermometers;
- thermomanometers;
- pressure sensors/transducers;
- pressure/temperature relays;
- valves;
- solenoid valves;
- thermowells;
- diaphragm seals;
- adapters;
- siphon tubes;
- accessories;
- hydrofilling service.

Irrelevant category examples:

- construction works;
- medical supplies;
- food;
- furniture;
- vehicles;
- fuel;
- uniforms;
- IT equipment if not related to KIP;
- office supplies;
- general repair services;
- unrelated industrial goods.

The unsupported list is not exhaustive and must remain configurable. Broad irrelevant categories should be handled as rules, not hardcoded forever.

## Manufacturer And Supplier Focus

Initial manufacturer/supplier focus:

- ROSMA;
- Fiztech;
- Manotom;
- similar instrumentation manufacturers.

Rules:

- manufacturer hint is not proof of exact match;
- manufacturer hint helps keep/review decision;
- no automatic substitution between manufacturers;
- analog or manufacturer alternatives require backend/rules/manager review;
- Tender Reader does not choose SKU or final supplier;
- manufacturer hints should be reported as `manufacturer_hints` and `matched_manufacturer_focus`.

## Decision Taxonomy

Tender Reader returns candidate classification only. Backend rules and manager review decide final tender status.

### `keep`

Use when:

- tender likely contains supplied KIP/instrumentation categories;
- product keywords match supported categories;
- manufacturer hints include ROSMA, Fiztech, Manotom, or similar instrumentation brands;
- deadlines are usable;
- no clear blocking category mismatch.

`keep` is not final approval to participate. It means the tender is likely worth manager attention.

### `needs_review`

Use when:

- product category is ambiguous;
- manufacturer hint is unclear;
- tender contains mixed categories;
- deadline or platform info is missing;
- product appears partially relevant;
- tender may require manager decision;
- LLM confidence is low;
- tender text is messy or incomplete;
- attachments are likely required for review.

`needs_review` should be preferred over guessing when the model is uncertain.

### `skip`

Use when:

- tender is likely irrelevant;
- product category is outside supplied scope;
- no supported instrumentation keywords are present;
- procurement is obviously non-KIP;
- relevance is low and there are no positive manufacturer/category hints.

`skip` is still candidate data. Backend policy may retain summary/audit or require manager sampling.

### `blocked_irrelevant`

Use when:

- tender is clearly out of scope;
- category is prohibited or impossible for Artmatika supply;
- there is no meaningful KIP relation;
- tender is duplicate, old, or canceled;
- tender is expired;
- tender region/customer constraints make it unusable according to versioned rules.

`blocked_irrelevant` is a stronger negative candidate than `skip`, but final blocking policy still belongs to backend/rules/manager workflow.

## Decision Output Schema

Conceptual output fields:

- `schema_version`;
- `agent_name`;
- `mode`;
- `source_email_ref`;
- `tender_candidate_ref`;
- `decision_candidate`;
- `decision_confidence`;
- `reason_summary`;
- `keep_reasons`;
- `skip_reasons`;
- `review_reasons`;
- `blocking_reasons`;
- `matched_positive_rules`;
- `matched_negative_rules`;
- `filter_version`;
- `product_keywords`;
- `manufacturer_hints`;
- `category_hints`;
- `buyer_name`;
- `procurement_region`;
- `tender_platform`;
- `tender_url_candidate`;
- `deadline_at`;
- `deadline_urgency`;
- `missing_fields`;
- `manager_questions`;
- `recommended_next_action`;
- `source_fragments`;
- `audit_ref`.

Example shape with placeholder values only:

```json
{
  "schema_version": "tender-reader-doc-v1",
  "agent_name": "mail_reader_agent",
  "mode": "tender_reader",
  "source_email_ref": "email:demo-tender-001",
  "tender_candidate_ref": "tender_candidate:demo-001",
  "decision_candidate": "needs_review",
  "decision_confidence": 0.71,
  "reason_summary": "Instrumentation keywords are present, but deadline and platform URL require manager review.",
  "keep_reasons": ["supported_category_hint:pressure_gauge"],
  "skip_reasons": [],
  "review_reasons": ["missing_platform_url", "deadline_requires_confirmation"],
  "blocking_reasons": [],
  "matched_positive_rules": ["rule:supported-instrumentation-keyword"],
  "matched_negative_rules": [],
  "filter_version": "tender-filter-doc-v1",
  "product_keywords": ["pressure gauge"],
  "manufacturer_hints": ["ROSMA"],
  "category_hints": ["pressure_gauge"],
  "buyer_name": "[demo buyer]",
  "procurement_region": "[demo region]",
  "tender_platform": "[demo platform]",
  "tender_url_candidate": "https://example.invalid/tender/demo",
  "deadline_at": null,
  "deadline_urgency": "unknown",
  "missing_fields": ["deadline_at"],
  "manager_questions": ["Уточнить срок подачи заявки и ссылку на площадку."],
  "recommended_next_action": "manager_review",
  "source_fragments": ["[demo source fragment]"],
  "audit_ref": "agent_run:demo-tender-reader-001"
}
```

## Deadline Urgency

Derived urgency values:

- `expired`;
- `today`;
- `tomorrow`;
- `within_3_days`;
- `within_7_days`;
- `later`;
- `unknown`.

Rules:

- expired tenders usually become `skip` or `blocked_irrelevant` unless manager override is allowed;
- near-deadline tenders may need escalation;
- unknown deadline usually requires `needs_review`;
- deadline parsing is candidate extraction and must be validated;
- no scheduler, reminder runtime, or notification engine is implemented here.

## Configurable Filter Rules

Tender filtering must be configurable and versioned. This documentation does not implement a rule engine.

### Positive Rules

Examples:

- contains KIP/instrumentation keywords;
- contains ROSMA, Fiztech, or Manotom hints;
- product types match supported catalog categories;
- buyer/region is acceptable;
- delivery terms are not obviously impossible;
- tender value is above internal threshold if future policy defines it.

### Negative Rules

Examples:

- unsupported category;
- expired tender;
- duplicate tender;
- canceled tender;
- unrelated service/procurement;
- unclear product with no KIP hints;
- prohibited category;
- missing deadline and low confidence.

### Review Rules

Examples:

- mixed categories;
- conflicting product hints;
- unclear manufacturer;
- missing buyer;
- missing platform URL;
- low confidence;
- attachments likely needed for review.

Versioned rule fields:

- `filter_version`;
- `rule_id`;
- `rule_name`;
- `rule_type`;
- `rule_weight`;
- `effective_from`;
- `effective_to`;
- `created_by_ref`;
- `audit_ref`.

Rules should be tuned by comparing false keep and false skip cases over time.

## Product Category Matching

Rules:

- category matching should use supplied instrumentation categories;
- LLM may identify keywords only;
- backend/rules validate final category policy;
- catalog matching is not performed by Tender Reader;
- Tender Reader does not choose SKU;
- Product Selector and Catalog Matcher may be used later only if tender is kept/needs_review and manager starts a workflow;
- mixed-category tenders should usually become `needs_review` unless unsupported categories clearly dominate and rules allow `skip` or `blocked_irrelevant`.

Category matching output should include:

- `product_keywords`;
- `category_hints`;
- `matched_supported_categories`;
- `matched_unsupported_categories`;
- `ambiguity_flags`;
- `source_fragments`.

## Manual Review Workflow

Manual review is the safety path for ambiguous or important tenders.

Future workflow concepts:

- `needs_review` creates a staff workspace item;
- manager opens extracted metadata;
- manager sees `reason_summary`, keep/skip/review/blocking reasons, matched rules, and source fragments;
- manager can override candidate decision;
- override requires reason and audit;
- manager can convert tender into internal request/task later;
- manager can assign responsible staff;
- manager can set reminder;
- manager can link documents;
- manager can run product extraction later;
- no automatic bid/offer generation.

Suggested manual actions:

- confirm keep;
- confirm skip;
- ask for more info;
- create internal tender task;
- create request card;
- assign manager;
- set reminder;
- link documents;
- run product extraction later.

No UI or workflow implementation is included.

## Relationship To Mail Reader Agent

Tender Reader can be a mode/subtype of Mail Reader Agent for MVP.

Rules:

- Mail Reader processes dirty customer request emails;
- Tender Reader processes tender notification emails;
- both extract candidate data;
- Tender Reader output schema is tender-specific;
- both require backend validation;
- neither writes final business data directly;
- both should record AgentRun audit data;
- Tender Reader mode should use `mode=tender_reader` or equivalent in future AgentRun metadata.

Allowed Tender Reader outputs:

- candidate tender metadata;
- candidate classification;
- reasons and matched rules;
- source fragments;
- manager questions;
- recommended next action.

Not allowed:

- final keep/skip decision;
- bid generation;
- КП generation;
- pricing;
- PDF/1C/invoice generation;
- scraping;
- tender submission.

## Future Tender Monitor Agent Boundary

Tender Reader mode may evolve into a separate Tender Monitor Agent if:

- tender volume grows;
- rules become complex;
- multiple tender platforms are integrated;
- monitoring schedules are needed;
- deadline alerts become central;
- document downloading/parsing becomes required.

Future Tender Monitor Agent would still not own final business truth.

Future Tender Monitor Agent may coordinate:

- scheduled tender source checks;
- platform connectors;
- deduplication;
- deadline monitoring;
- document collection workflows;
- notification/escalation triggers.

These are future boundaries only. No scheduler, scraping, connector, or platform integration is implemented here.

## Relationship To Staff Workspace

Related document: [Staff Workspace And Request Pipeline](STAFF_WORKSPACE_AND_PIPELINE.md).

Future integration concepts:

- kept/needs_review tenders can appear in staff workspace;
- skipped/blocked tenders may be stored as audit/summary only if policy allows;
- near-deadline tenders can become urgent tasks;
- responsible manager assignment is future workflow;
- tender task creation is future boundary;
- manager override should update activity timeline.

## Relationship To Notifications And SLA

Related document: [Notifications, Reminders And SLA Alerts](NOTIFICATIONS_REMINDERS_SLA.md).

Future integration concepts:

- `needs_review` tender can create notification;
- deadline soon can create alert;
- expired/canceled can avoid unnecessary alerts;
- reminders can be set manually;
- urgent tenders may escalate if policy allows;
- no scheduler, notification engine, reminder runtime, or SLA implementation is included.

## Relationship To Analytics

Related document: [CRM Analytics Dashboards](CRM_ANALYTICS_DASHBOARDS.md).

Future tender metrics may include:

- tenders received;
- kept;
- skipped;
- needs_review;
- blocked_irrelevant;
- deadline soon;
- expired;
- category distribution;
- manufacturer hints;
- region distribution;
- buyer distribution;
- manual override rate;
- false keep rate;
- false skip rate;
- eventually participated/won/lost if future workflow supports it.

Analytics backend is not implemented in this task.

## Relationship To Commercial Offer, Supplier Quote, And Document Center

Related documents:

- [Commercial Offer Lifecycle](COMMERCIAL_OFFER_LIFECYCLE.md)
- [Supplier Quote Workflow](SUPPLIER_QUOTE_WORKFLOW.md)
- [CRM Document Center](CRM_DOCUMENT_CENTER.md)

Rules:

- Tender Reader does not create КП;
- kept tender may later become request/task;
- supplier quote may be requested later by manager;
- tender attachments/documents are document center future boundary;
- automatic PDF/Excel/1C generation is forbidden in ART-40;
- supplier request and commercial offer workflows must start only through manager/backend workflow after tender review.

## LLM Boundaries

Strict rules:

- LLM cannot scrape tender sites;
- LLM cannot download tender documents;
- LLM cannot submit bids;
- LLM cannot generate final bid/offer;
- LLM cannot create final КП/PDF/invoice/1C documents;
- LLM cannot calculate price, VAT, totals, margin, or delivery;
- LLM cannot confirm SKU/catalog item;
- LLM cannot final-approve tender relevance;
- LLM cannot access credentials/secrets;
- LLM output is candidate data only;
- backend/rules/manager decides final workflow.

## Audit And Quality

Future audit fields:

- `source_email_ref`;
- `agent_run_ref`;
- `model_name`;
- `mode`;
- `mode_version`;
- `prompt_version`;
- `filter_version`;
- `candidate_decision`;
- `confidence`;
- `matched_rules`;
- `reasons`;
- `manager_override`;
- `override_reason`;
- `final_decision`;
- `timestamp`;
- `actor`;
- `source_fragments`.

Quality notes:

- false keep and false skip should be evaluated separately;
- false skip can be commercially dangerous;
- keep/needs_review precision matters to avoid manager overload;
- rule tuning must be versioned;
- ambiguous cases should go to `needs_review`;
- quality checks should compare candidate decision to manager final decision when available;
- source fragments should explain why classification happened.

## Security And Privacy

Rules:

- no real tender/customer data in docs;
- tender email content may include buyer/customer info and must be handled under privacy policy;
- notification previews must not leak sensitive data;
- attachments should not be parsed/downloaded automatically;
- LLM should receive minimized email content when possible;
- secrets, credentials, tokens, private keys, and passwords must never enter prompts or logs;
- Tender Reader must not access mailbox credentials directly;
- source fragments should be minimized and redacted if needed.

## Deferred Implementation

Explicitly deferred:

- email connectors;
- mailbox/folder integration;
- tender site scraping;
- backend jobs;
- cron/scheduler;
- parser code;
- API endpoints;
- database schema;
- SQL;
- ORM;
- migrations;
- UI;
- notifications runtime;
- analytics backend;
- document downloading;
- document parsing;
- OCR;
- pricing;
- КП generation;
- bid generation;
- bid submission;
- invoice/PDF/1C;
- dependencies;
- containers;
- Ollama/model changes;
- `.env.example` changes;
- real tender emails;
- real customer data;
- credentials;
- secrets;
- business logic.

## Non-Goals For ART-AGENT-007

This task does not add:

- code;
- backend services;
- frontend UI;
- API;
- database or migrations;
- parser;
- scheduler;
- email integration;
- scraping;
- tender platform integration;
- pricing;
- КП/PDF/1C/invoice generation;
- dependencies;
- containers;
- `.env.example` changes;
- credentials or secrets;
- real examples with real buyer/tender data.

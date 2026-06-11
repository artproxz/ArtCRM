# CRM Document Center

This document defines the documentation-only architecture for ArtCRM document center and file lifecycle beyond chat attachments.

It does not implement file storage, upload/download APIs, preview generation, scanning, OCR, parsing, frontend UI, backend APIs, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real files, real customer data, real supplier data, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM needs a document center separate from chat attachments because requests, quotes, supplier quotes, invoices, certificates, passports, contracts, tender files, customer specification files, catalog import files, stock import files, and price import files need controlled lifecycle, versions, visibility, permissions, retention, and audit.

Chat attachments are message-linked files. The document center is a broader controlled document layer for CRM entities and customer/supplier/commercial workflows. A chat attachment may later be promoted or linked to the document center, but it must not automatically become customer-visible.

Customer-visible vs internal-only visibility must be explicit. File storage, malware scanning, OCR, parsing, preview generation, and LLM document access are future boundaries and require separate implementation tasks.

## Scope

Covered here:

- document center concept;
- files linked to request, cart, quote, customer, supplier, catalog item, tender, and import workflows;
- document categories;
- versioning;
- permissions and visibility;
- customer-visible vs internal-only files;
- download/view audit;
- retention policy;
- relationship to ART-46 internal CRM attachments;
- future scanning/OCR/parsing boundaries.

Not covered here:

- file storage implementation;
- upload/download APIs;
- scanning/OCR/parsing;
- database schema;
- frontend UI;
- real files;
- business logic.

## Commercial Data And Flexible Permissions

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can be granted additional commercial, document, or supplier permissions if company policy allows.
- Manager can receive selected Director-level publish/export/sensitive-document functions if explicitly granted.
- Manager Assistant can receive the same document workflow functions as Manager or selected elevated functions if explicitly granted.
- Administrator does not automatically see purchase prices, supplier discounts, margins, supplier responses, or commercial documents unless permission allows it.
- Director can have commercial overview but may lack operational document edit/delete/publish actions unless explicitly granted.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive document capabilities require explicit permissions:

- view purchase price;
- view supplier discount;
- view margin;
- export quote;
- export sensitive commercial data;
- view supplier quote response;
- download internal commercial document;
- publish customer-visible document;
- unpublish customer-visible document;
- delete document;
- view audit;
- allow agent access to document content.

This principle extends [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md). No permission engine is implemented in this task.

## Document Center Concept

The document center is a controlled file/document layer for CRM.

It can store or link:

- customer specification files;
- quote PDF/Excel exports;
- supplier quote responses;
- invoices;
- contracts;
- certificates;
- passports;
- manuals;
- internal files;
- tender files;
- catalog import files;
- stock import files;
- price import files;
- customer attachments;
- supplier attachments.

Rules:

- documents are linked to owner entities;
- documents can have versions;
- visibility scope is explicit;
- customer visibility requires explicit publish action;
- internal-only and commercial-sensitive documents must not leak to customers;
- sensitive document actions must be audited.

## Linked Entity Contexts

Documents may be linked to:

- request;
- request position;
- cart;
- quote;
- quote version;
- customer organization;
- customer user/contact;
- supplier;
- supplier quote request;
- supplier quote response;
- catalog item;
- catalog publication;
- stock import;
- price import;
- tender;
- internal task;
- internal messenger thread/message.

The document does not own the business entity. Entity permissions and document permissions must both be considered in future backend enforcement.

## Document Object

Conceptual fields:

- `document_id`;
- `document_type`;
- `title`;
- `owner_entity_type`;
- `owner_entity_id`;
- `visibility_scope`;
- `current_version_ref`;
- `created_by_ref`;
- `created_at`;
- `retention_policy_id`;
- `audit_ref`.

No database schema or persistence implementation is added.

## Document Version Object

Conceptual fields:

- `document_version_id`;
- `document_id`;
- `version_number`;
- `original_file_name`;
- `stored_file_name`;
- `file_extension`;
- `mime_type`;
- `file_size_bytes`;
- `file_hash`;
- `storage_ref`;
- `scan_status`;
- `validation_status`;
- `created_by_ref`;
- `created_at`;
- `source_ref`;
- `audit_ref`.

Rules:

- file hash supports integrity, deduplication, and audit;
- storage reference must not expose local filesystem secrets or production storage details;
- old versions should remain auditable;
- current version is a pointer, not a reason to delete prior versions automatically.

## Document Categories

Document types:

- `certificate`;
- `passport`;
- `manual`;
- `specification`;
- `invoice`;
- `contract`;
- `commercial_offer`;
- `quote_export`;
- `supplier_response`;
- `supplier_quote_attachment`;
- `customer_attachment`;
- `internal_file`;
- `tender_file`;
- `catalog_import_file`;
- `stock_import_file`;
- `price_import_file`;
- `audit_export`.

Category rules:

- certificates, passports, and manuals can become public catalog documents if approved;
- commercial offers and quote exports must reference quote version snapshots;
- supplier responses are internal unless explicitly transformed into customer-facing fields;
- import files are internal operational records;
- audit exports are highly sensitive.

## Visibility Scopes

Visibility scopes:

- `internal_only`;
- `customer_visible`;
- `supplier_related_internal`;
- `staff_sensitive`;
- `commercial_sensitive`;
- `public_catalog_document`;
- `restricted_by_permission`;
- `archived`.

Rules:

- customer-visible documents must be explicitly marked/published;
- internal-only documents must never leak to customer portal;
- commercial-sensitive documents require explicit permissions;
- supplier responses are internal unless converted to customer-facing fields;
- catalog public documents may be shown on product cards if approved;
- archived documents remain auditable and should not be visible as active content by default;
- frontend hiding is not authorization.

## Allowed File Types And Validation

Initial allowed types should align with [Internal CRM Communication Center](CRM_TASK_MESSENGER.md):

- images: `.png`, `.jpg`, `.jpeg`, `.webp`;
- Word: `.doc`, `.docx`;
- PDF: `.pdf`;
- Excel: `.xls`, `.xlsx`.

Rules:

- allowlist required;
- MIME validation is a future boundary;
- file size limit is a future setting;
- file hash should be stored for integrity and audit;
- executable, script, and archive files should be blocked by default;
- preview generation is deferred;
- scan pipeline is deferred;
- upload/download APIs are deferred.

## Scanning, OCR, And Parsing Boundaries

Future boundaries:

- malware scanning;
- OCR;
- Excel/PDF/Word parsing;
- document preview generation;
- structured extraction;
- LLM-assisted document interpretation.

Rules:

- LLM cannot read document contents unless workflow and permissions explicitly allow it;
- parsed results require backend validation;
- file content must not be stored in prompts or logs without policy;
- secrets, credentials, tokens, private keys, and real customer/supplier data must not be exposed to prompts;
- parsing/OCR results are candidate data until validated by backend;
- suspicious or infected files must not be available for normal download.

Scan statuses:

- `not_required_for_mvp`;
- `pending`;
- `clean`;
- `suspicious`;
- `infected`;
- `scan_failed`;
- `quarantined`.

Validation statuses:

- `accepted`;
- `rejected_file_type`;
- `rejected_file_size`;
- `pending_scan`;
- `quarantined`;
- `deleted`.

## Permissions

Suggested permissions:

- `documents.view`;
- `documents.view_internal`;
- `documents.view_customer_visible`;
- `documents.view_commercial_sensitive`;
- `documents.upload`;
- `documents.download`;
- `documents.publish_customer_visible`;
- `documents.unpublish_customer_visible`;
- `documents.create_version`;
- `documents.delete_own`;
- `documents.delete_any`;
- `documents.archive`;
- `documents.restore`;
- `documents.export`;
- `documents.view_audit`;
- `documents.allow_agent_access`.

Flexible permission examples:

- Manager can publish customer-visible quote document if explicitly granted.
- Manager Assistant can upload supplier response attachment if explicitly granted.
- Administrator can manage storage/audit but not view commercial-sensitive files unless granted.
- Director can view sensitive commercial documents if granted, but may lack delete permissions.
- Role names are templates; explicit permissions decide access.

## Versioning

Versioning rules:

- documents can have versions;
- new quote export creates document version;
- replacing supplier response attachment creates a new version or related document;
- customer-visible documents should preserve sent snapshot;
- old versions remain auditable;
- deletion should be soft-delete or archival by default;
- hard delete should be restricted and audited if ever allowed;
- current version changes must be auditable.

## Customer-Facing Boundary

Rules:

- customers see only customer-visible documents;
- customers do not see internal supplier responses;
- customers do not see internal quote drafts;
- customers do not see purchase price or margin documents;
- customers do not see internal comments, matcher audit, or staff-only files;
- staff must explicitly publish documents to customer scope;
- publishing must be permission-protected and audited.

## Audit

Future audit events:

- document created;
- document version created;
- file uploaded;
- file downloaded;
- file viewed;
- file marked customer-visible;
- file unmarked customer-visible;
- file deleted;
- file archived;
- file restored;
- scan status changed;
- validation rejected;
- agent access requested;
- agent access granted;
- sensitive document viewed;
- sensitive document downloaded;
- commercial export created;
- access denied.

Audit records should capture actor, target document/version, owner entity, timestamp, permission used, previous/new state when relevant, source workflow, and request/session context when available.

## Retention

Retention rules:

- documents are business records;
- retention policy should be configurable;
- quote, customer, supplier, tender, and import documents may have different retention policies;
- deleted documents should remain auditable;
- hard delete should be restricted;
- storage lifecycle is deferred;
- retention rules must not bypass legal/business audit needs.

## Relationship To CRM Communication Center

The document center complements [Internal CRM Communication Center](CRM_TASK_MESSENGER.md).

Rules:

- chat attachments can later be promoted or linked to document center;
- document center can reference message/thread source;
- not every chat attachment is automatically customer-visible;
- customer-visible publishing requires explicit permission and audit;
- internal thread attachment visibility remains controlled by messenger and entity permissions.

## Relationship To Quote And Supplier Workflow

Relationship rules:

- quote PDF/Excel export becomes document center record in future;
- supplier response attachments become internal supplier-related documents;
- customer attachments from specification upload become customer/request-linked documents;
- certificates, passports, and manuals can be public catalog documents;
- quote exports should reference quote version snapshots;
- supplier attachments should not become customer-visible by default.

Related documents:

- [Commercial Offer Lifecycle](COMMERCIAL_OFFER_LIFECYCLE.md)
- [Supplier Quote Workflow](SUPPLIER_QUOTE_WORKFLOW.md)
- [Customer Marketplace Portal](CUSTOMER_MARKETPLACE_PORTAL.md)
- [Customer Organization Access](CUSTOMER_ORGANIZATION_ACCESS.md)
- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)

## Deferred Implementation

Explicitly deferred:

- file storage;
- upload/download APIs;
- preview generation;
- scanning;
- OCR;
- parsing;
- backend APIs;
- frontend UI;
- database schema;
- SQL;
- ORM;
- migrations;
- tests;
- dependencies;
- containers;
- `.env.example` changes;
- real files;
- real customer data;
- real supplier data;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-DOCS-001

This task does not add:

- file storage service;
- upload/download endpoints;
- document preview;
- malware scanning;
- OCR;
- parser;
- LLM document reading;
- customer document UI;
- document database tables;
- production files.

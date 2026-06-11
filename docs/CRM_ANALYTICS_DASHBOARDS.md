# CRM Analytics And Management Dashboards

This document defines the documentation-only architecture for ArtCRM analytics and management dashboards for directors, managers, manager assistants, administrators, and future staff.

It does not implement dashboard UI, analytics backend, SQL/reporting queries, BI integration, data warehouse, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real business data, real metrics, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM needs analytics so management and staff can understand operational health: request volume, response speed, overdue work, quote conversion, supplier bottlenecks, tender outcomes, product demand, missing catalog/stock, and commercial risk.

Director and management dashboards help control the business. Manager dashboards help individual employees understand their own workload and performance. Analytics should connect request pipeline, commercial offers, supplier quotes, tenders, SLA events, catalog matching, marketplace activity, stock/price freshness, and internal workflow status.

Margin, purchase prices, supplier discounts, sensitive exports, and staff performance metrics must be permission-protected and auditable.

## Scope

Covered here:

- analytics dashboard concept;
- director dashboard;
- manager performance dashboard;
- manager assistant dashboard;
- administrator dashboard;
- request funnel;
- response time and SLA metrics;
- overdue, blocked, and waiting supplier metrics;
- quote conversion metrics;
- margin and discount analytics as protected data;
- product demand analytics;
- missing stock / unavailable request analytics;
- supplier response metrics;
- tender metrics;
- export boundaries and permissions;
- data freshness;
- audit.

Not covered here:

- dashboard UI;
- analytics backend;
- SQL/reporting queries;
- BI integration;
- data warehouse;
- database schema;
- real business data;
- real metrics;
- business logic.

## Flexible Permission Principle

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can receive additional analytics or dashboard permissions if company policy allows.
- Manager can receive selected Administrator-level or Director-level analytics functions if explicitly granted.
- Manager Assistant can receive the same functions as Manager or selected elevated analytics functions if explicitly granted.
- Administrator does not automatically see all commercial analytics unless permission allows it.
- Director does not automatically perform every operational action unless permission allows it.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive analytics capabilities require special permissions, including:

- view purchase prices;
- view supplier discounts;
- view margin;
- view analytics;
- view director dashboard;
- export data;
- export sensitive analytics;
- view staff performance;
- view audit;
- import, publish, or roll back catalog, stock, and price versions.

This principle extends [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md). No analytics permissions are implemented here.

## Analytics Dashboard Concept

Analytics dashboards are future views over operational data. They should support decision-making without exposing sensitive details to users who lack permissions.

Dashboard data may later come from:

- request pipeline statuses;
- request positions;
- quote drafts and sent quotes;
- accepted/rejected outcomes;
- supplier quote requests and responses;
- tender classifications;
- SLA alerts and reminders;
- catalog matching results;
- product demand and unavailable requests;
- catalog, stock, and price import freshness;
- customer marketplace activity;
- internal communication/task events.

Exact data model, storage, queries, aggregation jobs, BI tools, and UI are deferred.

## Dashboard Audiences

### Director Dashboard

May include:

- request volume;
- requests by status;
- overdue requests;
- SLA breaches;
- quote conversion;
- accepted/rejected quotes;
- revenue estimate if future pricing allows;
- margin overview if permission allows;
- discount usage if permission allows;
- manager workload;
- manager response speed;
- waiting supplier bottlenecks;
- tender performance;
- popular products;
- unavailable demand;
- import freshness warnings;
- security/audit alerts if permission allows.

Director dashboard access is permission-based. A Manager can receive selected director dashboard widgets if explicitly granted.

### Manager Dashboard

May include:

- own active requests;
- own overdue requests;
- own quote drafts;
- own supplier waiting items;
- own reminders;
- own messages/mentions;
- own quote conversion;
- own SLA performance;
- own customer replies;
- own tenders to review.

Manager analytics should be scoped by assignment, team, and permissions. A Manager may receive team or director-level analytics if explicitly granted.

### Manager Assistant Dashboard

Manager Assistant dashboard may equal Manager dashboard if permissions allow. Differences must be permission-based, not hardcoded by role name.

Possible examples:

- same own/team request workload as Manager;
- same reminders and messages as Manager;
- selected quote preparation widgets;
- selected director-level risk widgets if granted.

### Administrator Dashboard

May include:

- system health summary;
- import status;
- future integration status;
- audit/security events if permission allows;
- user access issues.

Administrator does not automatically see commercial analytics such as margin, purchase price, supplier discount, or customer commercial performance unless permission allows it.

## Request Funnel Metrics

Conceptual funnel:

- request received;
- cleaned / triaged;
- product selection;
- catalog matched;
- supplier quote requested;
- quote drafted;
- quote approved;
- quote sent;
- accepted;
- rejected;
- canceled;
- archived.

Metrics:

- count;
- conversion rate;
- average time in stage;
- median time in stage;
- stuck items;
- drop-off reason;
- owner/team breakdown if permission allows;
- source breakdown such as mail, customer portal, tender, or manual entry if future data supports it.

Exact funnel logic and state mapping are deferred.

## SLA And Response Metrics

Potential metrics:

- first response time;
- time to product selection;
- time waiting supplier;
- time to quote draft;
- time waiting approval;
- time to quote sent;
- overdue count;
- SLA breach count;
- escalation count;
- risk count;
- paused SLA count;
- SLA override count.

Rules:

- metrics must identify the time window used;
- pause/override events must be visible in audit and explained;
- staff performance views require permission;
- Director-level SLA metrics may be granted to Manager or Manager Assistant if policy allows.

## Quote Analytics

Potential metrics:

- quotes created;
- quotes sent;
- quotes accepted;
- quotes rejected;
- expired quotes;
- quote conversion;
- discount usage;
- approval time;
- average quote preparation time;
- customer response time;
- quote revisions;
- quote approval rejections.

Sensitive analytics:

- margin;
- purchase price;
- supplier discount;
- manual discount amount;
- commercial terms;
- sensitive exports.

Sensitive quote analytics require explicit permissions and audit. This task does not implement pricing, quote lifecycle, totals, invoices, PDFs, or commercial offer generation.

## Product Demand Analytics

Potential metrics:

- most requested product types;
- most requested ranges;
- most requested manufacturers;
- missing catalog matches;
- unavailable or low-stock demand;
- repeated customer requests;
- frequently requested accessories;
- analog requests;
- hydrofilling requests;
- related component demand;
- product lines that often need clarification.

Product demand analytics can later help improve catalog coverage, Product Selector quality, related component rules, and stock planning. Exact aggregation is deferred.

## Supplier Analytics

Potential metrics:

- supplier response time;
- supplier quote response rate;
- supplier overdue responses;
- supplier price/delivery changes;
- bottlenecks by supplier;
- request volume by supplier;
- supplier quote acceptance impact;
- ROSMA-specific tracking as initial supplier focus.

Supplier analytics may contain sensitive supplier conditions. Access must be permission-protected.

## Tender Analytics

Potential metrics:

- tenders received;
- keep / skip / needs_review counts;
- deadline soon;
- participated;
- won/lost if future workflow allows;
- reasons for skip/reject;
- categories/manufacturers requested;
- tender response speed;
- tender workload by manager/team.

Tender analytics may combine pipeline, deadline, supplier, and quote data. Exact workflow and metrics are deferred.

## Missing Stock And Unavailable Demand

Potential metrics:

- requests with no catalog match;
- requests with no stock;
- requests with quote-based availability;
- requests blocked by stale stock or price data;
- repeated unavailable product demand;
- missing related component demand;
- analog requests caused by unavailable direct items.

These metrics can later feed catalog/import improvement work and supplier follow-up. They must not expose internal purchase or supplier data without permissions.

## Export Boundaries

Rules:

- analytics export requires explicit permission;
- director-level exports require special permission;
- margin, discount, purchase price, supplier condition, and staff performance exports require high-sensitivity permission;
- exports must be audited;
- customer data in exports must respect privacy rules;
- export payload must not contain secrets, credentials, tokens, private keys, full prompts, or model paths;
- customer organization data must respect ownership and visibility rules.

Suggested permissions:

- `analytics.view_own`;
- `analytics.view_team`;
- `analytics.view_all`;
- `analytics.view_director_dashboard`;
- `analytics.view_margin`;
- `analytics.view_purchase_price`;
- `analytics.view_supplier_discount`;
- `analytics.view_staff_performance`;
- `analytics.export`;
- `analytics.export_sensitive`;
- `analytics.configure_dashboard`.

Flexible permission examples:

- Manager may receive selected director dashboard permissions if explicitly granted.
- Manager Assistant may receive team analytics if explicitly granted.
- Director may lack operational edit permissions if not granted.
- Administrator may view import status while lacking commercial margin analytics.
- Role name is not enough; permission grants determine access.

## Data Freshness

Analytics should show data freshness and source time windows.

Concepts:

- analytics based on current operational data;
- catalog, stock, and price import freshness matters;
- stale stock/price data should be flagged;
- metrics should show last updated time;
- active catalog publication and latest stock/price snapshots should be referenced when relevant;
- future data warehouse or BI is deferred.

Freshness signals may include:

- `last_updated_at`;
- `source_publication_ref`;
- `stock_snapshot_ref`;
- `price_snapshot_ref`;
- `is_stale`;
- `staleness_reason`;
- `refresh_status`.

No refresh job or analytics pipeline is implemented here.

## Audit

Future audit events:

- dashboard viewed;
- director dashboard viewed;
- sensitive widget viewed;
- staff performance viewed;
- sensitive metric exported;
- analytics export created;
- analytics export downloaded;
- dashboard preference changed;
- analytics permission denied;
- analytics configuration changed;
- margin metric viewed;
- purchase price metric viewed;
- supplier discount metric viewed.

Audit records should capture actor, target dashboard/metric, timestamp, filters/time window, export format when relevant, permission used, and request/session context when relevant.

## Relationship To Staff Workspace

Analytics supports the operational workspace documented in [Staff Workspace And Request Pipeline](STAFF_WORKSPACE_AND_PIPELINE.md).

Examples:

- request pipeline statuses feed funnel metrics;
- waiting supplier items feed bottleneck metrics;
- overdue requests feed SLA metrics;
- quote drafts and quote sent statuses feed conversion;
- manager workload widgets may use analytics summaries;
- director overview widgets may use aggregated pipeline and SLA data.

## Relationship To Notifications And SLA

Analytics can use events from [Notifications, Reminders And SLA Alerts](NOTIFICATIONS_REMINDERS_SLA.md):

- SLA warnings;
- SLA overdues;
- reminders completed or missed;
- escalations;
- notification delivery failures;
- high-risk alerts.

Notification and SLA runtime implementation is deferred.

## Relationship To Catalog And Marketplace

Analytics may later consume data from:

- [Catalog Data Model](CATALOG_MODEL.md);
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md);
- [Customer Marketplace Portal](CUSTOMER_MARKETPLACE_PORTAL.md);
- [Customer Organization Access](CUSTOMER_ORGANIZATION_ACCESS.md).

Rules:

- customer portal activity must respect privacy and organization visibility;
- catalog and matcher metrics must not expose internal matcher audit to customers;
- stock and price freshness must be shown carefully and permission-protected when sensitive.

## Deferred Implementation

Explicitly deferred:

- dashboard UI;
- analytics backend;
- SQL/reporting queries;
- BI integration;
- data warehouse;
- aggregation jobs;
- cache layer;
- websocket/realtime;
- database schema;
- SQL;
- ORM;
- migrations;
- tests;
- dependencies;
- containers;
- real metrics;
- real business data;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-ANALYTICS-001

This task does not add:

- analytics service code;
- dashboard screens;
- SQL queries;
- reports;
- BI connector;
- export runtime;
- staff performance calculations;
- revenue/margin calculations;
- database schema;
- `.env.example` changes.

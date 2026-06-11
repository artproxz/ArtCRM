# Staff Workspace And Request Pipeline

This document defines the documentation-only architecture for the internal ArtCRM staff workspace, request pipeline, manager dashboard, and director overview.

It does not implement frontend UI, kanban, backend APIs, pipeline engine, SLA engine, notification engine, scheduler, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real business data, credentials, tokens, secrets, or business logic.

## Purpose

The staff workspace is the operational command center for ArtCRM employees. It should help managers, manager assistants, directors, administrators, and future staff understand what requires attention now: new requests, overdue work, blocked items, supplier waiting, quote drafts, approvals, customer replies, tenders, reminders, and internal tasks.

Managers need a daily working screen because request processing involves multiple sources and handoffs:

- customer marketplace carts and quote requests;
- incoming mail and Mail Reader output;
- Product Selector candidate data;
- Backend Catalog Matcher decisions;
- supplier quote requests and ROSMA responses;
- quote drafts and approvals;
- internal CRM communication threads;
- notifications, reminders, and SLA alerts.

The workspace must be permission-based. Role names such as Director, Administrator, Manager, and Manager Assistant are default templates only. Effective access to widgets, requests, actions, analytics, commercial data, assignment, and override functions must be determined by explicit permissions and enforced by the backend later.

## Scope

Covered here:

- staff workspace concept;
- request queue and inbox;
- kanban/pipeline by conceptual status;
- priorities;
- SLA and reaction time boundaries;
- responsible manager and manager assistant assignment;
- today, overdue, blocked, waiting supplier, and waiting customer views;
- quick actions;
- manager dashboard widgets;
- director overview widgets;
- audit and activity timeline;
- customer request context;
- linked carts, quotes, and supplier quotes;
- integration with the Internal CRM Communication Center;
- permission model.

Not covered here:

- frontend UI implementation;
- kanban implementation;
- backend APIs;
- pipeline engine;
- SLA engine implementation;
- notification engine implementation;
- database schema;
- SQL, ORM, or migrations;
- business logic.

## Flexible Permission Principle

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can be granted additional permissions if company policy allows.
- Manager can receive selected Administrator-level or Director-level functions when explicitly granted.
- Manager Assistant can receive the same functions as Manager or selected elevated functions when explicitly granted.
- Administrator does not automatically see all commercial data unless permission allows it.
- Director does not need to perform every operational action unless permission allows it.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive capabilities require special permissions, including:

- view purchase prices;
- view supplier discounts;
- view margin;
- approve manual discount;
- export data;
- view analytics;
- view director dashboard;
- assign responsible manager;
- override SLA;
- manage notification rules for others;
- view staff performance;
- view audit;
- import, publish, or roll back catalog, stock, and price versions;
- view internal CRM threads;
- delete or edit other users' messages;
- manage users and permissions.

This principle extends [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md). No permission enforcement is implemented in this task.

## Staff Workspace Concept

The staff workspace is an operational command center. It should aggregate work by urgency, ownership, status, communication, and next action.

Primary areas:

- inbox / new requests;
- assigned to me;
- assigned to my team;
- waiting for supplier;
- waiting for customer;
- waiting for manager action;
- waiting for approval;
- overdue;
- blocked;
- today;
- tenders;
- quote drafts;
- supplier quote requests;
- customer carts / requests;
- internal tasks.

The workspace should not decide access by screen placement. Every item and action must be filtered by backend permissions in future implementation.

## Request Queue And Inbox

The request queue is the conceptual entry point for new and active work. It may include:

- new customer quote requests from marketplace carts;
- incoming mail-derived request cards;
- requests that need triage;
- requests waiting for Product Selector review;
- requests waiting for Catalog Matcher review;
- supplier response follow-ups;
- customer clarifications;
- approval tasks;
- tender-related work.

Queue ordering may later depend on priority, SLA risk, assignment, customer importance, tender deadline, and current blocker state. Exact sorting and queue logic are deferred.

## Request Pipeline

Pipeline statuses are conceptual. Exact workflow state machine, transition guards, automations, and persistence are deferred.

Suggested statuses:

- `new`;
- `triage`;
- `needs_cleaning`;
- `product_selection`;
- `catalog_matching`;
- `needs_clarification`;
- `waiting_supplier`;
- `supplier_response_received`;
- `quote_draft`;
- `quote_approval`;
- `quote_sent`;
- `waiting_customer`;
- `accepted`;
- `rejected`;
- `canceled`;
- `archived`.

Pipeline rules:

- statuses are conceptual labels for future workflow design;
- exact state machine is deferred;
- status changes must be auditable;
- pipeline visibility depends on permissions;
- staff can only see or act on requests according to permissions;
- frontend kanban visibility is not authorization;
- backend must enforce status-change permissions later.

## Assignment Model

Conceptual assignment roles:

- responsible manager;
- manager assistant;
- watchers;
- director observer;
- support/admin assignee;
- assignment history;
- reassignment audit.

Manager Assistant can have the same functional baseline as Manager if permissions allow. Differences must be represented as permission grants or revokes, not hardcoded by role name.

Flexible assignment permissions may include:

- `request.assign_self`;
- `request.assign_manager`;
- `request.assign_assistant`;
- `request.reassign_any`;
- `request.view_assigned`;
- `request.view_team`;
- `request.view_all`;
- `request.change_status`;
- `request.override_status`;
- `request.close`;
- `request.reopen`.

Assignment changes must capture actor, previous assignment, new assignment, reason when available, timestamp, and permission used.

## SLA And Priority Boundaries

SLA and reaction time are documented as future concepts. This task does not implement SLA calculation, timers, schedulers, alerts, or escalations.

Priority concepts:

- low;
- normal;
- high;
- urgent;
- tender-critical.

SLA concepts:

- first response SLA;
- quote preparation SLA;
- supplier waiting pause;
- customer waiting pause;
- overdue state;
- risk state;
- escalation state.

Suggested conceptual fields:

- `priority`;
- `sla_started_at`;
- `first_response_due_at`;
- `quote_due_at`;
- `sla_paused_reason`;
- `sla_status`;
- `escalation_level`.

Rules:

- SLA can be calculated later by a dedicated backend service;
- SLA pauses and overrides require explicit permission;
- SLA changes must be audited;
- supplier/customer waiting pauses must be visible and explainable;
- escalations must respect permissions and ownership;
- Director-level SLA views can be granted to Manager or Manager Assistant if policy allows.

## Staff Quick Actions

Quick actions are future UI/workflow actions, not implemented behavior.

Potential actions:

- run Mail Reader / re-clean request if needed;
- run Product Selector;
- run Catalog Matcher;
- open catalog candidate list;
- request exact information from ROSMA or another supplier;
- create supplier quote request draft;
- create quote draft;
- request approval;
- send quote to customer;
- ask customer clarification;
- create internal task;
- open internal chat;
- attach document;
- schedule reminder;
- assign or reassign responsible staff;
- mark as waiting supplier or waiting customer;
- open analytics context.

Every quick action requires permission. Suggested permission names:

- `agent.mail_reader.run`;
- `agent.product_selector.run`;
- `matcher.run`;
- `catalog_candidates.view`;
- `supplier_quote.create`;
- `quote.create_draft`;
- `quote.request_approval`;
- `quote.send`;
- `request.ask_clarification`;
- `task.create`;
- `messenger.create_message`;
- `attachments.upload`;
- `notifications.create_reminder`;
- `request.assign_manager`;
- `request.assign_assistant`;
- `analytics.view_context`.

## Manager Dashboard Widgets

Manager dashboard widgets are future views for daily work. They may include:

- my new requests;
- my overdue requests;
- waiting supplier;
- supplier response received;
- quote drafts needing work;
- quote approvals waiting;
- customer replies waiting;
- tenders needing review;
- today tasks;
- reminders;
- messages / mentions;
- performance snapshot.

Widget visibility must depend on explicit permissions and entity access. Manager Assistant may receive the same dashboard widgets as Manager if permission allows.

## Director Overview Widgets

Director overview widgets are future management views. They may include:

- request volume;
- overdue by manager or team;
- waiting supplier count;
- quote conversion;
- margin / discount overview if permission allows;
- manager workload;
- tender performance;
- response speed;
- blocked requests;
- approvals waiting;
- risk alerts.

Director dashboard access is permission-based. A Manager can receive selected Director-level widgets if explicitly granted. A Director may lack operational edit actions unless explicitly granted.

## Activity Timeline

The activity timeline is an auditable request history. It may include:

- request created;
- assigned;
- reassigned;
- priority changed;
- status changed;
- Product Selector run;
- Catalog Matcher run;
- supplier quote requested;
- supplier response received;
- quote draft created;
- approval requested;
- quote approved or rejected;
- quote sent;
- customer response;
- reminder created;
- internal message created;
- document attached;
- SLA paused or overridden;
- permission-sensitive action performed.

Timeline events should capture actor, timestamp, target entity, previous/new state when relevant, permission used, and source service/agent when relevant.

## Customer Request Context

A staff request view may need context from:

- customer marketplace cart or request;
- customer organization and customer user;
- request positions;
- Product Selector output;
- Backend Catalog Matcher decision;
- related component suggestions;
- analog review state;
- supplier quote requests and responses;
- quote drafts and commercial offer lifecycle;
- internal CRM communication thread;
- files and attachments;
- reminders and notifications.

Customer-facing status must remain separate from internal pipeline status. Internal comments, supplier responses, purchase prices, discounts, margins, and staff discussions must not leak to customer portal.

## Linked Carts, Quotes, And Supplier Quotes

Conceptual relationships:

- customer cart can become a customer request;
- request can have multiple request positions;
- request can have quote draft(s);
- quote draft can require approval;
- request or position can have supplier quote request(s);
- supplier quote response can update manager review context;
- accepted/rejected quote outcome can feed analytics later.

This document does not implement these relationships, database tables, API contracts, or business rules.

## Internal Communication Center Integration

The workspace should link to [Internal CRM Communication Center](CRM_TASK_MESSENGER.md).

Integration concepts:

- open entity-linked chat from request;
- show mentions and unread state if permissions allow;
- create internal task from message in the future;
- attach documents from request context if permissions allow;
- audit message and attachment actions;
- keep customer-visible data separate from internal staff threads.

Staff workspace must not expose internal threads to customer portal. LLM agents must not read internal threads unless a workflow and permission explicitly allow it.

## Permission Examples

Examples of flexible access:

- Manager receives `analytics.view_director_dashboard` for selected widgets while still lacking `users.assign_permission`.
- Manager Assistant receives `quote.send` and `supplier_quote.create`, matching Manager workflow capability.
- Administrator receives `users.manage` and `audit.view_security` but not `prices.view_purchase_price` or `analytics.view_margin`.
- Director receives `analytics.view_all` and `analytics.view_margin` but not `request.change_status` if operational editing is not part of policy.

These are documentation examples only. No permissions are implemented.

## Relationship To Other Docs

Related documents:

- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Internal CRM Communication Center](CRM_TASK_MESSENGER.md)
- [Customer Marketplace Portal](CUSTOMER_MARKETPLACE_PORTAL.md)
- [Customer Organization Access](CUSTOMER_ORGANIZATION_ACCESS.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)
- [Agent Platform](AGENT_PLATFORM.md)
- [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md)
- [Notifications, Reminders And SLA Alerts](NOTIFICATIONS_REMINDERS_SLA.md)
- [CRM Analytics Dashboards](CRM_ANALYTICS_DASHBOARDS.md)

## Deferred Implementation

Explicitly deferred:

- UI;
- frontend implementation;
- kanban implementation;
- pipeline engine;
- backend APIs;
- SLA engine;
- notification engine;
- scheduler;
- realtime/websocket;
- database schema;
- SQL;
- ORM;
- migrations;
- integrations;
- tests;
- dependencies;
- containers;
- real business data;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-CRM-002

This task does not add:

- staff workspace UI;
- manager dashboard UI;
- director dashboard UI;
- kanban board;
- request workflow implementation;
- assignment implementation;
- status transition implementation;
- SLA timers;
- quick action handlers;
- notification runtime;
- analytics backend;
- database schema;
- `.env.example` changes.

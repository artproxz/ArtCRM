# Notifications, Reminders And SLA Alerts

This document defines the documentation-only architecture for ArtCRM notification center, reminders, and SLA alerts.

It does not implement notification runtime engine, scheduler, reminders runtime, email/push/browser integrations, websocket/realtime, frontend UI, backend APIs, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real business data, real metrics, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM staff should not lose operational signals: new requests, assignment changes, overdue reactions, supplier quote responses, chat mentions, approvals, tender deadlines, import review tasks, customer replies, and security notices.

A notification center gives each employee a controlled place to see what needs attention. Reminders help staff schedule follow-up work. SLA alerts highlight response and quote preparation risks before requests become overdue.

Notifications must be permission-aware. A user can receive notifications only for objects they may access. Reminder and SLA logic must be auditable because notification storms, hidden alerts, or silent SLA overrides can affect customer service quality and management visibility.

## Scope

Covered here:

- notification center concept;
- reminders;
- SLA/reaction alerts;
- new request notifications;
- assignment notifications;
- chat mentions from [Internal CRM Communication Center](CRM_TASK_MESSENGER.md);
- supplier quote response notifications;
- quote approval, sent, accepted, and rejected notifications;
- tender keep / needs_review notifications;
- import review notifications;
- user preferences;
- quiet hours;
- mute;
- channels;
- audit;
- anti-spam boundaries;
- flexible permission model.

Not covered here:

- notification runtime engine;
- scheduler implementation;
- email/push/browser integrations;
- websocket/realtime;
- database schema;
- frontend UI;
- backend APIs;
- business logic.

## Flexible Permission Principle

Roles are templates, not hardcoded limits.

Rules:

- Director, Administrator, Manager, Manager Assistant, and other staff roles are default role templates.
- Any role can receive additional notification, reminder, SLA, or director-level alert permissions if company policy allows.
- Manager can receive selected Administrator-level or Director-level notification functions if explicitly granted.
- Manager Assistant can receive the same notification functions as Manager or selected elevated functions if explicitly granted.
- Administrator does not automatically see all commercial notifications unless permission allows it.
- Director does not automatically perform every operational notification action unless permission allows it.
- Permission grants and revokes must be auditable.
- Permission checks must be enforced by the backend later, not by frontend visibility.

Sensitive notification capabilities require special permissions, including:

- manage notification rules for others;
- view director dashboard alerts;
- view staff performance alerts;
- override SLA;
- pause SLA;
- configure SLA rules;
- view audit;
- export notification or SLA reports;
- view internal CRM thread notifications;
- view purchase price, supplier discount, margin, or commercial-risk notifications.

This principle extends [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md). No permission enforcement is implemented here.

## Notification Center Concept

The notification center is a future staff-facing inbox for operational signals.

Possible notification states:

- `unread`;
- `read`;
- `dismissed`;
- `snoozed`;
- `action_required`;
- `resolved`;
- `failed_delivery`.

Possible notification metadata:

- target entity type;
- target entity reference;
- severity;
- category;
- created_at;
- delivered_at;
- read_at;
- action link target;
- audit reference;
- permission required to view.

The notification center is not a substitute for authorization. If a user loses access to the target entity, the notification should not reveal restricted content.

## Notification Types

Conceptual notification categories:

- `new_request`;
- `request_assigned`;
- `request_reassigned`;
- `status_changed`;
- `sla_warning`;
- `sla_overdue`;
- `supplier_quote_response_received`;
- `supplier_quote_overdue`;
- `quote_approval_required`;
- `quote_approved`;
- `quote_rejected`;
- `quote_sent`;
- `customer_reply_received`;
- `chat_mention`;
- `direct_message`;
- `group_message`;
- `scheduled_message_failed`;
- `tender_needs_review`;
- `tender_deadline_soon`;
- `catalog_import_review_required`;
- `stock_import_review_required`;
- `price_import_review_required`;
- `system_security_notice`.

Rules:

- notification text must not expose secrets, credentials, tokens, full prompts, or private keys;
- commercial details such as purchase price, supplier discount, and margin must appear only when the recipient has permission;
- customer data in notification previews must respect entity access and privacy rules;
- notification routing must be audited for sensitive events.

## Reminder Model

Conceptual reminder object:

- `reminder_id`;
- `owner_user_ref`;
- `target_entity_type`;
- `target_entity_id`;
- `remind_at`;
- `message`;
- `status`;
- `created_by_ref`;
- `created_at`;
- `completed_at`;
- `canceled_at`;
- `audit_ref`.

Reminder statuses:

- `active`;
- `sent`;
- `completed`;
- `snoozed`;
- `canceled`;
- `failed`.

Reminder rules:

- reminders can target requests, quotes, supplier quote requests, customer replies, tenders, tasks, chats, or other future CRM entities;
- reminder owner must have access to the target entity;
- creating a reminder for another user or team requires permission;
- snooze, complete, and cancel actions must be audited;
- reminder content must not contain secrets or credentials;
- scheduler/runtime behavior is deferred.

Suggested reminder permissions:

- `notifications.create_reminder`;
- `notifications.create_reminder_for_others`;
- `notifications.snooze`;
- `notifications.complete_reminder`;
- `notifications.cancel_reminder`;
- `notifications.view_team_reminders`.

## SLA Alert Model

SLA alerts are future operational signals based on deadlines and risk thresholds.

Conceptual SLA alert dimensions:

- first response due;
- quote preparation due;
- supplier response due;
- tender deadline due;
- approval due;
- warning threshold;
- overdue threshold;
- escalation level;
- pause reason.

Suggested conceptual fields:

- `sla_alert_id`;
- `target_entity_type`;
- `target_entity_id`;
- `sla_type`;
- `due_at`;
- `warning_threshold_at`;
- `overdue_at`;
- `status`;
- `escalation_level`;
- `paused`;
- `pause_reason`;
- `owner_user_ref`;
- `responsible_team_ref`;
- `audit_ref`.

Rules:

- SLA alerts depend on permissions and ownership;
- SLA pause requires permission;
- SLA override requires permission;
- SLA configuration requires permission;
- warning and overdue events must be auditable;
- supplier waiting and customer waiting pauses must be explainable;
- exact timer calculation is deferred to a future SLA engine.

## User Preferences

Future preference concepts:

- notification channels;
- in-app notification;
- future email notification;
- future browser push;
- mute chat;
- mute entity;
- quiet hours;
- do-not-disturb;
- priority-only mode;
- digest mode.

Rules:

- preferences are personal unless admin policy allows management;
- personal preferences cannot bypass mandatory high-risk policy alerts unless company policy allows it;
- notification preferences must not grant access to objects the user cannot view;
- preference changes should be audited when they affect required operational alerts.

No preference UI, delivery engine, email, browser push, or websocket implementation is included.

## Channels

Conceptual channel types:

- in-app notification center;
- in-app badge/counter;
- future email;
- future browser push;
- future digest summary;
- future integration channel if explicitly designed later.

Rules:

- in-app notifications are the baseline concept;
- external channels are deferred;
- channel payload must be minimized and permission-aware;
- sensitive data must not be pushed to channels that are not approved for that data class.

## Permission Flexibility

Suggested permissions:

- `notifications.view`;
- `notifications.view_all`;
- `notifications.create_reminder`;
- `notifications.create_reminder_for_others`;
- `notifications.snooze`;
- `notifications.manage_own_preferences`;
- `notifications.manage_team_preferences`;
- `notifications.manage_system_rules`;
- `sla.view`;
- `sla.view_team`;
- `sla.view_all`;
- `sla.override`;
- `sla.pause`;
- `sla.configure_rules`;
- `alerts.view_director_level`;
- `audit.view_notification_events`.

Examples:

- Manager may receive `alerts.view_director_level` for selected risk alerts if explicitly granted.
- Manager Assistant may receive the same SLA and reminder capabilities as Manager if policy allows.
- Administrator may manage system notification templates only if `notifications.manage_system_rules` is granted.
- Administrator does not automatically see all commercial alert details without commercial permissions.
- Director may receive high-level SLA views while lacking operational `sla.override` if not granted.

## Notification Visibility Rules

Visibility rules:

- user can receive only notifications for objects they may access;
- notification previews must not leak hidden fields;
- commercial fields require commercial permissions;
- internal CRM thread notifications require messenger/thread permissions;
- director dashboard alerts may be granted to Manager or Manager Assistant if policy allows;
- service/system notifications should be scoped to responsible staff and technical users with permissions.

Backend enforcement is required in future implementation. Frontend hidden badges are not authorization.

## Audit

Future audit events:

- notification created;
- notification delivered;
- notification read;
- notification dismissed;
- notification snoozed;
- reminder created;
- reminder snoozed;
- reminder completed;
- reminder canceled;
- SLA warning created;
- SLA overdue created;
- SLA paused;
- SLA resumed;
- SLA overridden;
- escalation created;
- notification preference changed;
- system notification rule changed;
- access denied to notification target;
- sensitive alert viewed.

Audit records should capture actor, target entity, timestamp, previous/new state when relevant, permission used, delivery channel, and reason when available.

## Anti-Spam And Safety Boundaries

Conceptual anti-spam controls:

- deduplication;
- throttling;
- digest mode;
- notification storm detection;
- per-user limits;
- per-entity limits;
- grouping repeated events;
- system priority levels;
- escalation throttling;
- high-risk alert policy.

Rules:

- duplicate events should not flood staff;
- grouped notifications should still preserve audit events;
- high-risk alerts cannot be silently hidden without approved policy;
- quiet hours should not suppress mandatory critical alerts unless policy allows it;
- failed delivery should be visible/auditable for critical notifications.

## Relationship To Staff Workspace

Notifications feed the staff workspace documented in [Staff Workspace And Request Pipeline](STAFF_WORKSPACE_AND_PIPELINE.md).

Examples:

- new request notification can place an item in staff inbox;
- SLA warning can make a request appear in `today` or `risk` views;
- supplier response received can move an item into manager attention;
- chat mention can surface from the Internal CRM Communication Center;
- reminder can create a daily action item.

Exact UI and runtime behavior are deferred.

## Relationship To Internal CRM Communication Center

Notifications should connect to [Internal CRM Communication Center](CRM_TASK_MESSENGER.md) for:

- chat mentions;
- direct messages;
- group messages;
- scheduled message failures;
- muted chat behavior;
- unread counters;
- message-linked tasks.

Internal chat notifications must not expose customer data or commercial information to users who lack permissions. Customers and guests cannot see internal CRM thread notifications.

## Relationship To Analytics

SLA warning and overdue events can later feed [CRM Analytics Dashboards](CRM_ANALYTICS_DASHBOARDS.md):

- overdue count;
- SLA breach count;
- escalation count;
- response speed metrics;
- manager workload and performance;
- tender deadline performance.

Analytics use is documentation-only here and must respect permissions.

## Deferred Implementation

Explicitly deferred:

- scheduler;
- notification engine;
- reminder runtime;
- SLA engine;
- email integration;
- push/browser notification integration;
- websocket/realtime;
- digest generator;
- notification UI;
- backend APIs;
- database schema;
- SQL;
- ORM;
- migrations;
- tests;
- dependencies;
- containers;
- real data;
- real metrics;
- credentials;
- tokens;
- secrets;
- business logic.

## Non-Goals For ART-NOTIFY-001

This task does not add:

- notification sending;
- reminders runtime;
- SLA calculation;
- alert delivery;
- websocket/realtime;
- email/push/browser integrations;
- frontend notification center;
- database tables;
- SQL/reporting queries;
- `.env.example` changes.

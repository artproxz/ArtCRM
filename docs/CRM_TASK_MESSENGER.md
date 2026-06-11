# Internal CRM Communication Center

This document defines the documentation-only architecture for the internal ArtCRM Communication Center: entity-linked chats, direct staff chats, group staff chats, support tab, messages, attachments, images, rich text, emoji, scheduled messages, and auto-replies.

It does not implement UI, API endpoints, backend services, websocket/realtime delivery, file upload, image upload, file download, file storage, antivirus/scanning, OCR, parsing, notifications, scheduler, delayed jobs, auto-reply engine, rich text editor, emoji picker, search index, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real files, real customer data, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM needs an internal CRM Communication Center because one flat comment area inside a card is not enough for operational work. Requests, quotes, supplier quote responses, matcher decisions, tenders, imports, and internal tasks often need focused discussions with different participants, attachments, audit needs, and visibility boundaries.

The Communication Center is staff/internal communication, not customer-facing chat. Customer authentication and guest access are documented separately in [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md). Customer users and guests must not see internal CRM threads by default.

The architecture must be linked to CRM entities so context is preserved: every entity-linked chat has a clear parent entity, and the parent entity controls the base visibility context. Messenger permissions then add action-level control.

Access to chats and files must be controlled by RBAC because internal messages can contain customer details, commercial context, purchase prices, supplier discounts, matcher review notes, and staff decisions. LLM agents must not read internal discussions without explicit permission and workflow reason. Attachments require a separate security boundary because file content, previews, downloads, scans, and future parsing can expose sensitive data.

## Scope

Covered here:

- Chats for purchasing, tenders, tasks, requests, quotes, supplier quotes, matcher review, product selection review, and import review.
- Direct staff chats.
- Group staff chats.
- Support tab.
- Thread model.
- Message model.
- Attachment model.
- Images.
- Emoji.
- Rich text formatting.
- Scheduled messages.
- Auto-reply.
- Navigation and UI placement concept.
- Permissions.
- Audit.
- Data retention.
- LLM agent visibility boundary.

Not covered here:

- Real messenger UI.
- Websocket/realtime implementation.
- Backend API endpoints.
- File storage implementation.
- File upload/download implementation.
- Antivirus/scanning implementation.
- OCR/parsing implementation.
- Notification system implementation.
- Scheduler/delayed jobs implementation.
- DB schema/migrations.
- Customer-facing chat implementation.

## Communication Center Concept

ArtCRM Communication Center is an internal communication layer for CRM work. It groups staff conversations by business context and by staff communication needs.

### Entity-Linked Chats / Work Chats

Entity-linked chats are attached to CRM entities. Each entity-linked chat must have an explicit `parent_entity_ref` represented conceptually by `parent_entity_type` and `parent_entity_id`.

Supported parent contexts:

- Purchase.
- Tender.
- Task.
- Request.
- Cart.
- Quote / quote draft.
- Supplier quote request.
- Supplier quote response.
- Catalog Matcher execution.
- Product Selector output.
- Catalog import review.
- Stock import review.
- Price import review.
- Future custom entity.

Rules:

- Thread does not own the parent entity.
- Parent entity controls base visibility context.
- Messenger permissions control actions such as view, message, edit, delete, attach, download, schedule, export, and search.
- Entity permission and messenger permission are both required.

### Direct Staff Chats

Direct staff chats are private staff-to-staff conversations such as:

- Manager with manager assistant.
- Manager with director.
- Administrator with employee.
- Any staff user with any other staff user according to permissions.

Rules:

- Direct chat creation requires a future permission such as `messenger.create_direct_chat`.
- Direct chat visibility is limited to participants unless an elevated permission and policy allow access.
- Director or Administrator access is not automatic and must be permission-based.
- Direct staff chats must not become visible to all staff by default.
- Access to direct chats must be auditable.

### Group Staff Chats

Group staff chats are staff-only multi-participant conversations.

Capabilities to design later:

- Create group chat.
- Invite staff participants.
- Remove participants.
- Use group roles: `creator`, `group_admin`, `member`.
- Discuss departments, projects, periods, or operational workstreams.
- Audit participant add/remove events.

Rules:

- Group visibility is limited to participants unless elevated permission and policy allow access.
- Group administration does not imply access to unrelated commercial data.
- Participant management must be auditable.

### Support Tab

The `Support` tab is an internal CRM support channel.

Purpose:

- Staff can ask Administrator/CRM support for help.
- Support threads are internal staff support, not customer-facing support.
- Customer-facing support chat is not implemented in ART-46.
- If customer support chat is needed later, it must be a separate architecture and a separate task.

## Navigation And UI Placement Concept

This is a concept only; no UI is implemented in ART-46.

The chat surface may open as:

- Compact popup window.
- Full-screen chat view.
- Right-side panel.
- Right-side tab inside CRM.
- Collapsible/expandable panel.

The future UI should support switching between chats and clear navigation.

Primary tabs:

- `Work Chats` - purchases, tenders, tasks, requests, quotes, supplier quote, matcher/import review.
- `Personnel` - direct and group staff chats.
- `Support` - internal support channel.

Future UI states:

- Active chat.
- Pinned chats.
- Favorite chats.
- Archived chats.
- Muted chats.
- Unread counters.
- Search results.
- Compact popup mode.
- Full-screen mode.
- Right-panel mode.

## Thread Model

Conceptual thread fields:

- `thread_id`
- `thread_type`
- `parent_entity_type`
- `parent_entity_id`
- `title`
- `status`
- `created_by_ref`
- `created_at`
- `last_message_at`
- `visibility_scope`
- `participant_refs`
- `pinned_by_refs`
- `muted_by_refs`
- `archived_by_refs`
- `retention_policy_id`
- `audit_ref`

Possible `thread_type` values:

- `entity_linked`
- `direct_staff`
- `group_staff`
- `support`
- `system`

Possible `thread_status` values:

- `active`
- `archived`
- `locked`
- `read_only`
- `deleted_soft`

These are conceptual fields only. This document does not create database schema.

## Message Model

Conceptual message fields:

- `message_id`
- `thread_id`
- `author_user_ref`
- `author_role_snapshot`
- `message_body`
- `message_format`
- `rich_text_payload`
- `created_at`
- `edited_at`
- `deleted_at`
- `delete_reason`
- `visibility_scope`
- `reply_to_message_id`
- `mentioned_user_refs`
- `attachments[]`
- `reactions[]`
- `pinned`
- `scheduled_send_at`
- `sent_at`
- `delivery_status`
- `read_state`
- `audit_ref`

Message capabilities:

- Plain text.
- Rich text.
- Bold.
- Italic.
- Color/highlight.
- Emoji.
- Reactions.
- Replies.
- Mentions.
- Pinned messages.
- Image attachments.
- Word/PDF/Excel attachments.
- Message drafts.
- Scheduled messages.
- Auto-replies.
- Out-of-office replies.

Rules:

- Message belongs to exactly one thread.
- Author must be auditable.
- Edit/delete must be auditable.
- Internal messages are not customer-visible by default.
- Message visibility is controlled by thread visibility and RBAC permissions.

## Rich Text And Emoji

Future formatting support:

- Bold.
- Italic.
- Color.
- Highlight.
- Emoji/smiles.
- Links.
- Line breaks.
- Quoted replies.

Security notes:

- Rich text must be sanitized in future implementation.
- No raw HTML rendering without sanitization.
- Links must be treated carefully.
- Color/highlight is presentation only and must not represent authorization or workflow status.

No rich text editor is implemented in ART-46.

## Image And File Attachments

Conceptual attachment fields:

- `attachment_id`
- `thread_id`
- `message_id`
- `uploaded_by_ref`
- `original_file_name`
- `stored_file_name`
- `file_extension`
- `mime_type`
- `file_size_bytes`
- `file_hash`
- `storage_ref`
- `scan_status`
- `validation_status`
- `preview_status`
- `created_at`
- `deleted_at`
- `delete_reason`
- `audit_ref`

Allowed initial file categories:

### Images

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

### Word

- `.doc`
- `.docx`

### PDF

- `.pdf`

### Excel

- `.xls`
- `.xlsx`

Rules:

- File type allowlist required.
- MIME validation required in future.
- File extension alone is not enough.
- File size limit required.
- File hash should be stored for integrity, deduplication, and audit.
- Image preview is a future boundary.
- Malware scanning is a future boundary.
- OCR/parsing is a future boundary.
- File content must not be parsed by LLM agents unless workflow and permissions explicitly allow it.

No file upload, storage, or scanning is implemented in ART-46.

## Attachment Security

Attachment security concepts:

- Max file size policy as future configurable setting.
- Allowed MIME types.
- Executable, script, and archive types blocked by default.
- Future malware scanning.
- Quarantine state.
- Rejected state.
- Scan pending state.
- Audit download events for sensitive files.
- Attachment ownership and access control.
- Deletion policy.

Suggested conceptual `scan_status` values:

- `not_required_for_mvp`
- `pending`
- `clean`
- `suspicious`
- `infected`
- `scan_failed`
- `quarantined`

Suggested conceptual `validation_status` values:

- `accepted`
- `rejected_file_type`
- `rejected_file_size`
- `pending_scan`
- `quarantined`
- `deleted`

## Scheduled And Automatic Messages

### Scheduled Messages

Future capabilities:

- User can schedule message delivery for a future date/time.
- Example: send tomorrow at 12:00.
- Scheduled messages must be visible to author before send.
- Author can edit/cancel before send if permission allows.
- Scheduled message should be audited on create, edit, cancel, and send.
- Timezone handling must be defined in future implementation.
- Delivery failure state should be considered.

Conceptual fields:

- `scheduled_message_id`
- `thread_id`
- `author_user_ref`
- `message_payload`
- `scheduled_send_at`
- `timezone`
- `status`
- `created_at`
- `updated_at`
- `sent_at`
- `canceled_at`
- `audit_ref`

Suggested status values:

- `draft`
- `scheduled`
- `sent`
- `canceled`
- `failed`

### Auto-Reply

Future capabilities:

- User can configure auto-reply.
- Out-of-office style message.
- Active time window.
- Optional target scope: direct chats only, group chats, support chats.
- Auto-reply must avoid spam loops.
- Auto-reply events must be auditable.
- Auto-reply content must follow the same formatting/security rules as normal messages.

Conceptual fields:

- `auto_reply_rule_id`
- `owner_user_ref`
- `enabled`
- `message_body`
- `active_from`
- `active_to`
- `scope`
- `created_at`
- `updated_at`
- `audit_ref`

No scheduler, delayed jobs, auto-reply engine, or notifications are implemented in ART-46.

## Useful Future Capabilities

Future capabilities:

- Mute chat.
- Archive chat.
- Pin chat.
- Favorite/star chat.
- Unread counters.
- Notification preferences.
- Read receipts as optional future feature.
- Search in chat.
- Message drafts.
- Create task from message.
- Create supplier quote follow-up from message.
- Link message to CRM entity.
- Convert chat message into internal note.
- Export chat only with elevated permission.
- System messages for status changes.
- System messages for assignment changes.
- System messages for supplier response updates.
- System messages for matcher decision changes.

No implementation is included in ART-46.

## Visibility And Access Rules

Rules:

- Internal thread is visible only to staff users with relevant permissions.
- Customer users cannot see internal CRM threads by default.
- Guest users cannot see internal CRM threads.
- Service/system actors cannot read threads unless explicitly allowed.
- LLM agents cannot read internal messages by default.
- Staff visibility must depend on entity access and messenger permissions.
- Direct chat visibility is limited to participants unless elevated permission applies.
- Group chat visibility is limited to participants unless elevated permission applies.
- Support chat visibility is limited by support/admin permissions.

Existing ART-44 permissions:

- `messenger.view_thread`
- `messenger.create_message`
- `messenger.edit_own_message`
- `messenger.delete_own_message`
- `messenger.edit_any_message`
- `messenger.delete_any_message`
- `attachments.upload`
- `attachments.view`
- `attachments.download`
- `attachments.delete_own`
- `attachments.delete_any`
- `agent.view_internal_threads`

Conceptual future permissions:

- `messenger.create_direct_chat`
- `messenger.create_group_chat`
- `messenger.invite_participant`
- `messenger.remove_participant`
- `messenger.view_staff_chat`
- `messenger.schedule_message`
- `messenger.configure_auto_reply`
- `messenger.pin_message`
- `messenger.pin_chat`
- `messenger.archive_chat`
- `messenger.mute_chat`
- `messenger.export_chat`
- `messenger.search`
- `attachments.upload_image`

Rule: frontend hiding is not authorization. Backend must enforce access later.

## Role Behavior

### Director

Director may have:

- Broad visibility into internal threads if permission allows.
- Audit visibility.
- Ability to view/delete messages if permission allows.
- Visibility into sensitive commercial discussions if permission allows.
- Ability to export chats only with explicit permission.

### Administrator

Administrator may manage technical access and support chats, but:

- Does not automatically see all commercial/internal staff chats.
- Needs explicit permission for sensitive threads.
- May have attachment administration permissions if allowed.

### Manager

Manager may:

- Read/write internal messages on assigned/visible requests.
- Create direct/group chats if permission allows.
- Participate in staff chats.
- Attach files/images if permission allows.
- Edit/delete own messages if permission allows.
- View supplier quote, matcher, tender, or import related threads if permissions allow.

### Manager Assistant

Important:

- Manager assistant can have the same functional baseline as manager.
- Differences are permission-based, not hardcoded.
- Access to chats and attachments must be configurable.

### Customer

Customer cannot see internal CRM messenger threads by default. Customer-facing chat is out of scope and should be a separate future architecture.

### Guest

Guest has no access to CRM chats.

### Service/System Actor / LLM Agent

Rules:

- No default access to internal chats.
- No default access to direct staff chats.
- No default access to group staff chats.
- Explicit workflow permission required.
- Access must be auditable.
- Agent must receive only scoped/minimized data.
- Agent must not receive secrets, purchase prices, supplier discounts, or internal commercial comments unless explicit workflow permission allows it.

## Editing And Deletion Rules

Rules:

- Users can edit own messages only if `messenger.edit_own_message`.
- Users can delete own messages only if `messenger.delete_own_message`.
- Editing/deleting any message requires elevated permissions.
- Deleted messages should preferably become soft-deleted for audit.
- Hard delete should be restricted and likely avoided for business/audit reasons.
- Attachment deletion must be audited.
- Delete reason should be captured for elevated deletion.

## Audit Events

Future audit events:

- Thread created.
- Thread linked to parent entity.
- Direct chat created.
- Group chat created.
- Participant invited.
- Participant removed.
- Message created.
- Message edited.
- Message deleted.
- Scheduled message created.
- Scheduled message edited.
- Scheduled message canceled.
- Scheduled message sent.
- Auto-reply configured.
- Auto-reply enabled/disabled.
- Auto-reply sent.
- Attachment uploaded.
- Image uploaded.
- Attachment viewed.
- Attachment downloaded.
- Attachment deleted.
- Attachment rejected by validation.
- Attachment quarantined.
- Access denied to thread.
- Access denied to attachment.
- Chat exported.
- Agent requested internal chat access.
- Agent received internal chat data.
- Permission-sensitive action performed.

Audit event should capture:

- Actor.
- Action.
- Target entity.
- Timestamp.
- Permission used.
- Previous/new state when relevant.
- Request/session context when relevant.

## Data Retention

Rules:

- Internal chats are business records.
- Retention policy should be configurable.
- Entity-linked chats should be retained with parent entity.
- Direct/group chats require separate retention policy.
- Support chats require separate retention policy.
- Deleted messages should remain auditable as soft-deleted records.
- Attachments may require retention/legal policy.
- Future storage lifecycle rules are deferred.

## Relationship To CRM Entities

Thread can link to:

- Request.
- Cart.
- Quote.
- Supplier quote request.
- Supplier quote response.
- Matcher execution.
- Product Selector output.
- Tender item.
- Catalog import review.
- Price import review.
- Stock import review.

Rules:

- Thread does not own parent entity.
- Parent entity controls base visibility context.
- Messenger permissions add action-level control.
- Entity permission and messenger permission are both required.

## Notifications Boundary

Future notification concepts:

- Notification when message is posted.
- Mention notifications.
- Unread counters.
- Browser notification.
- Email notification only if explicitly designed later.
- User notification preferences.
- Mute chat support.

Notifications are not implemented in ART-46.

## Realtime Boundary

Concepts:

- Future websocket/realtime delivery may be added.
- Initial architecture does not require realtime.
- Polling or refresh can be enough later.
- No websocket implementation is included in ART-46.

## LLM Agent Visibility Boundary

Rules:

- Agents do not read any internal chats by default.
- This includes entity-linked chats, direct staff chats, and group staff chats.
- Agent access requires explicit permission and workflow reason.
- Agent access must be logged.
- Agent access should use data minimization.
- Attachments/images are not sent to agents unless explicitly allowed.
- Agents must not see secrets, purchase prices, supplier discounts, or internal commercial comments unless workflow and permissions allow.
- If agent summarizes a chat later, output must be marked as generated and auditable.

## Customer-Facing Boundary

Rules:

- This is not customer chat.
- Customer cannot see internal chats.
- Customer cannot see staff direct/group chats.
- Future customer-facing messaging/support, if needed, must be separate architecture.
- Internal staff notes must not leak to customer portal or customer PDF/KP.

## Relationship To Other Docs

Related documents:

- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Agent Platform](AGENT_PLATFORM.md)
- [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md)

## Deferred Implementation

The following work is explicitly deferred:

- Messenger UI.
- Popup window.
- Full-screen chat.
- Right-side panel.
- Chat switching UI.
- Backend API endpoints.
- Websocket/realtime.
- File upload.
- Image upload.
- File download.
- File storage.
- Antivirus/malware scanning.
- OCR.
- Document parsing.
- Attachment preview.
- Notification system.
- Mentions implementation.
- Unread counters implementation.
- Scheduled message scheduler.
- Delayed jobs.
- Auto-reply engine.
- Rich text editor.
- Emoji picker.
- Search index.
- Chat export implementation.
- DB schema.
- SQL.
- ORM.
- Migrations.
- Tests.
- Permissions enforcement implementation.
- Customer-facing chat.

## Non-Goals For ART-CRM-001

This task does not add:

- UI.
- API endpoints.
- Backend implementation.
- Websocket/realtime.
- File upload.
- Image upload.
- File download.
- Storage implementation.
- Antivirus/scanning.
- OCR.
- Parsing.
- Notifications.
- Scheduler.
- Delayed jobs.
- Auto-reply engine.
- Rich text editor.
- Emoji picker.
- Search index.
- DB schema.
- SQL.
- ORM.
- Migrations.
- Tests.
- New dependencies.
- Containers.
- `.env.example` changes.
- Real files.
- Real customer data.
- Credentials.
- Tokens.
- Secrets.
- Business logic.

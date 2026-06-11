# Security, RBAC and Access Control Architecture

This document defines the documentation-only security, RBAC, and access-control baseline for ArtCRM before final architecture review and before business logic implementation begins.

It does not implement auth code, middleware, database schema, SQL, ORM, migrations, frontend screens, admin UI, rate limiting, WAF/CDN/proxy config, OAuth/email integration, password reset, real users, real emails, secrets, tokens, credentials, or production configuration.

## Purpose

ArtCRM will store the company's operational working base: customers, requests, carts, commercial conditions, catalog data, stock, prices, supplier discounts, purchase prices, files, internal discussions, agent outputs, Catalog Matcher results, and supplier quote requests/responses. Security must be designed before business code so future implementation has explicit boundaries rather than ad hoc checks scattered through modules.

The baseline addresses these risks:

- DDoS and abusive traffic.
- Brute-force login attempts.
- Account takeover.
- Privilege escalation.
- Leakage of purchase prices.
- Leakage of supplier discounts.
- Unauthorized customer base export.
- Unauthorized file access.
- LLM-agent access to forbidden data.
- Accidental over-permissioning of staff.

Roles must not be plain text labels that directly unlock behavior. A role is only a starting template. Effective access must be permission-based, auditable, and revocable feature by feature. This is especially important because manager assistants may start with the same functional baseline as managers, while Director and Administrator need the ability to grant or remove specific capabilities later.

LLM agents must not bypass RBAC. Agents are service/system actors and need explicit permissions for the data and actions used by their workflow. Agent output remains auditable candidate data and must not become a shortcut around staff/customer isolation.

## Initial User Groups

Initial staff composition:

- Director.
- 2 main managers.
- 2 manager assistants.
- 1 administrator.
- Future staff/users.

System user categories:

- `staff user` - internal staff member working in CRM workflows.
- `customer user` - authenticated customer with access to only their own data.
- `guest user` - unauthenticated visitor limited to public catalog browsing.
- `service/system actor` - backend jobs, LLM agents, import runners, scheduler, Catalog Matcher, and future integrations.

## RBAC Model

ArtCRM should use a role-template plus explicit permission model:

- Role templates provide default permissions for common starting positions.
- Effective access is the union of role template permissions and explicitly granted permissions, minus explicitly revoked permissions.
- Sensitive permissions require audit records when granted, revoked, or used for sensitive actions.
- Staff/customer data boundaries must be enforced even when a user has broad functional permissions.
- Permission checks belong on backend boundaries before data is read, exported, updated, or passed to agents/services.
- Frontend visibility is a convenience layer only and must not be the source of authorization truth.

Roles to document as starting templates:

- `administrator`
- `director`
- `manager`
- `manager_assistant`
- `customer`
- `guest`
- `service/system_actor`

## Manager And Manager Assistant

`manager_assistant` is not a permanently reduced manager role. The default template can include the same functional surface as `manager`, and any differences must be configured permission by permission.

Rules:

- `manager_assistant` may have the same baseline functionality as `manager`.
- Feature access must be flexible and controlled by permissions.
- Director and Administrator can grant or revoke functionality according to policy.
- Manager assistant restrictions must not be hardcoded only because of the role name.
- Any difference between `manager` and `manager_assistant` should be represented as explicit permission changes.

## Director And Administrator Authority

### Director

The Director has business-administrative authority and may receive permissions to:

- Manage staff access.
- View commercial data.
- View purchase prices.
- View supplier discounts.
- View customer requests.
- View audit.
- Manage critical permissions.
- Grant and revoke staff functionality.
- Export business data when explicitly permitted.
- Publish or roll back commercial sources when explicitly permitted.

Director permissions carry high business sensitivity. Grant/revoke actions and sensitive exports must be audited.

### Administrator

The Administrator has technical access-management authority and may receive permissions to:

- Manage users.
- Help with access problems.
- Grant or revoke functionality according to the approved policy.
- Suspend or block users.
- Reset access.
- View technical audit events.

Important boundaries:

- Administrator does not automatically need access to all commercial data.
- Administrator permissions are also permission-based.
- Director may have higher business priority for sensitive commercial permissions such as purchase prices and supplier discounts.
- Technical user administration does not imply permission to view customer requests, margins, supplier discounts, or purchase prices unless explicitly granted.

## Permission Taxonomy

Permissions are functional capabilities. Names below are baseline contract names for future implementation; they are not implemented in this task.

### User And Access Management

- `users.view`
- `users.invite`
- `users.activate`
- `users.suspend`
- `users.revoke_access`
- `users.reset_access`
- `users.assign_role`
- `users.assign_permission`
- `users.revoke_permission`
- `users.view_audit`

### Requests And CRM Cards

- `requests.view`
- `requests.create`
- `requests.edit`
- `requests.assign_responsible`
- `requests.change_status`
- `requests.archive`
- `requests.export`
- `requests.view_all`
- `requests.view_own_only`

### Catalog

- `catalog.view`
- `catalog.view_private_fields`
- `catalog.import`
- `catalog.publish`
- `catalog.archive_version`
- `catalog.rollback_version`

### Stock

- `stock.view`
- `stock.import`
- `stock.publish`
- `stock.rollback_version`

### Pricing

- `prices.view_customer_price`
- `prices.view_purchase_price`
- `prices.view_supplier_discount`
- `prices.import`
- `prices.publish`
- `prices.apply_manual_discount`
- `prices.override_price`
- `prices.view_margin`

### Cart / Quote / Commercial Offer

- `cart.view`
- `cart.create`
- `cart.edit`
- `cart.submit`
- `quote.create_draft`
- `quote.edit`
- `quote.send_to_customer`
- `quote.approve`
- `quote.export`

### Supplier Quote / ROSMA Request

- `supplier_quote.create_request`
- `supplier_quote.send_request`
- `supplier_quote.view_response`
- `supplier_quote.apply_delivery_update`
- `supplier_quote.apply_price_update`

### Product Selector / Catalog Matcher

- `product_selector.run`
- `product_selector.view_result`
- `catalog_matcher.run`
- `catalog_matcher.view_result`
- `catalog_matcher.override_decision`
- `catalog_matcher.view_audit`

### Tenders

- `tenders.view`
- `tenders.classify`
- `tenders.keep`
- `tenders.skip`
- `tenders.needs_review`
- `tenders.export`

### Internal Messenger And Files

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

### Audit

- `audit.view`
- `audit.export`
- `audit.security_events.view`
- `audit.permission_events.view`

### Agents / Service Actors

- `agent.mail_reader.run`
- `agent.tender_reader.run`
- `agent.product_selector.run`
- `agent.response_draft.run`
- `agent.view_output`
- `agent.view_internal_threads`
- `agent.access_customer_data`
- `agent.access_price_data`

LLM-agent rules:

- LLM agents must not access data only because they are agents.
- Agents need explicit service/system permissions.
- Agents must not bypass staff/customer permissions.
- Agent outputs must be auditable.

## Default Role Templates

Role templates below are starting points. Future implementation must allow explicit permission changes per user or group.

### Guest

Guest can:

- Browse the catalog.
- Search the catalog.
- Open product cards.
- View public product-card information.

Guest cannot:

- Add items to a cart.
- Save a cart.
- Submit a request.
- Request a commercial offer.
- View personal conditions.
- View request history.
- View internal comments.
- View purchase prices.
- View supplier discounts.

To add an item to a cart, the user must authenticate. Guest/customer cart conversion and customer authentication details are planned for ART-45.

### Customer

Customer can:

- Authenticate.
- Add items to cart.
- Save or submit cart.
- Create a request or commercial-offer request.
- View own carts.
- View own requests.
- View own history.
- Attach files if future policy allows it.
- View only own data.

Customer cannot:

- View internal CRM threads.
- View purchase prices.
- View supplier discounts.
- View internal supplier quote responses.
- View other customers' requests.
- View staff audit.

### Manager

Manager can work with customer-facing and internal request workflows:

- Work with requests.
- Work with carts.
- Use Product Selector.
- Use Catalog Matcher.
- Request precise information from ROSMA.
- Create commercial-offer drafts.
- Participate in internal discussions.
- Attach files.
- Apply manual discounts if permission is granted.
- View purchase prices if permission is granted.
- View supplier discounts if permission is granted.

### Manager Assistant

Manager assistant can start with the same functional baseline as manager:

- Same baseline functionality can be granted as for manager.
- Differences must be configured permission by permission.
- The role must not be hardcoded as a reduced role.
- The role is a starting template for later access configuration.

### Director

Director template includes broad business oversight:

- Full business access when explicitly permitted.
- Permission management.
- Critical commercial data.
- Audit.
- Export.
- Publishing or rollback of commercial sources when explicitly permitted.

### Administrator

Administrator template focuses on technical access management:

- User and access management.
- Blocking and unblocking.
- Access reset.
- Technical audit.
- No automatic full access to commercial data without separate permissions.

### Service/System Actor

Service/system actor covers non-human execution contexts:

- Backend jobs.
- Import runner.
- LLM agents.
- Catalog Matcher.
- Scheduler.
- Future integrations.

Rule: each service/system actor receives only the minimum permissions required for the workflow it performs.

## Account Lifecycle

Account states:

- `invited` - user has been invited but has not started activation.
- `pending_activation` - user has started activation and awaits verification or completion.
- `active` - user can authenticate and use granted permissions.
- `suspended` - access is temporarily disabled.
- `revoked` - access has been withdrawn and sessions must be invalidated.
- `archived` - historical account record retained for audit without active access.

Account actions:

- Invite user.
- Activate user.
- Suspend user.
- Revoke user.
- Restore user.
- Reset access.
- Rotate credentials/session.
- Force logout.

Sensitive lifecycle transitions must be audited, including who performed the action, target user, timestamp, reason when available, and affected permissions/roles.

## Authentication Requirements

This section defines conceptual requirements only. Implementation is deferred.

### Staff Authentication

- Staff login required.
- Strong password policy or external identity provider may be selected later.
- MFA recommended for Director and Administrator.
- Session expiration required.
- Refresh/session rotation required.
- Successful login audit required.
- Failed login audit required.
- Brute-force protection required.
- Password/credential storage must never store plaintext passwords or secrets; final hashing, storage, and provider decisions are deferred to implementation tasks.

### Customer Authentication

- Customer login required to add items to cart and submit request.
- Future email verification, magic-link, or OAuth-like email integration is deferred.
- Customer sees only own data.
- Customer session expiration required.
- Guest-to-customer cart conversion is handled in planned follow-up ART-45.

### Guest Access

- No login required for catalog browsing/product cards.
- Guest access must be rate limited.
- No add-to-cart.
- No submit request.
- No personal data access.

## Anti-Abuse / Anti-DDoS / Rate Limiting Boundaries

Conceptual controls:

- Rate limiting per IP.
- Rate limiting per user/session.
- Login attempt throttling.
- Temporary account lock or challenge after too many failed attempts.
- Guest catalog scraping limits.
- Cart/action limits.
- Attachment upload limits.
- API request throttling.
- Future WAF/CDN/proxy boundary.
- Audit of suspicious activity.
- Separate limits for staff, customer, guest, and service actors.

This task does not implement a rate limiter. It only defines the architectural boundary so future backend/API work can enforce limits consistently.

## Session Security

Session requirements:

- Sessions expire after configured lifetime.
- Refresh/session rotation concept required.
- Logout invalidates current session.
- Forced logout after revoke or suspend.
- Device/session audit for staff and sensitive users.
- Session invalidation after critical permission changes.
- Privilege-sensitive changes may require session refresh or re-authentication in future implementation.

## Sensitive Data Classification

### Data Classes

- Public catalog data.
- Customer-owned data.
- Staff internal data.
- Commercial data.
- Supplier price/purchase price.
- Supplier discount.
- Audit/security events.
- Attached documents.
- Agent outputs.
- Internal messages.

### Visibility Rules

- Guest users may view public catalog data only.
- Customer users may view their own customer-owned data and public catalog data.
- Managers and manager assistants may view staff workflow data and customer requests according to permissions.
- Purchase prices, supplier discounts, margin data, and supplier quote responses require explicit commercial permissions.
- Director may receive broad business access according to approved permissions.
- Administrator may view technical audit and access-management data, but commercial visibility requires separate permissions.
- Service/system actors may access only data explicitly required by their workflow permissions.
- LLM agents may receive only scoped input data approved for the workflow and must not receive secrets or unauthorized commercial data.

## Permission Audit

Audit events to record in future implementation:

- Role assigned.
- Role removed.
- Permission granted.
- Permission revoked.
- User suspended.
- User reactivated.
- User access revoked.
- Failed login.
- Successful login.
- Suspicious activity.
- Data export.
- Price source publication.
- Stock/catalog publication.
- Manual discount applied.
- Supplier quote response applied.

Permission audit entries should capture actor, target, action, timestamp, reason when available, previous state, new state, and request/session context when appropriate.

## LLM Agent Security Boundaries

LLM agents are service/system actors and must follow the same access-control model as other backend services.

Rules:

- Agents need explicit permissions.
- Agents must not read internal messenger threads by default.
- Agents must not access prices or supplier discounts unless explicitly allowed.
- Agents must not bypass customer/staff isolation.
- Agent outputs must be auditable.
- Prompt/output storage must not include secrets.
- Stored config/logs must not include filesystem model paths.
- Agent outputs remain candidate data unless a backend validation service and authorized user/workflow approve them.

## Attachment And File Security Boundary

Detailed file and internal messenger architecture is planned for ART-46. Baseline rules:

- File uploads require permissions.
- File type allowlist required.
- File size limits required.
- Future malware scanning required.
- File access audited.
- LLM agents cannot read attachments unless workflow policy explicitly allows it.

## Relationship To Other Docs

Related existing documents:

- [Agent Platform](AGENT_PLATFORM.md)
- [Agent JSON Schemas and DTO Contracts](AGENT_JSON_SCHEMAS.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)

Planned follow-ups:

- `CUSTOMER_AUTH_AND_GUEST_ACCESS.md` is planned for ART-45.
- `CRM_TASK_MESSENGER.md` is planned for ART-46.

## Deferred Implementation

The following work is explicitly deferred:

- Auth backend.
- RBAC middleware.
- DB schema/migrations.
- Frontend login/admin screens.
- Customer auth screens.
- Email verification.
- Magic-link/OAuth.
- Password reset.
- Rate limiter.
- WAF/CDN/proxy config.
- File scanning.
- Production security configuration.
- Real users/roles/secrets.

## Non-Goals For ART-SEC-001

This task does not add:

- Auth code.
- Backend middleware.
- Frontend UI.
- Admin panel.
- DB schema.
- SQL.
- ORM.
- Migrations.
- Rate limiter.
- WAF/CDN/proxy config.
- OAuth/email/magic-link implementation.
- Password reset implementation.
- Tests.
- Dependencies.
- Containers.
- `.env.example` changes.
- Secrets.
- Credentials.
- Tokens.
- Real emails.
- Real users.
- Production configuration.
- Business logic.

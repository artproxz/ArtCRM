# Customer Organization Access

This document defines the documentation-only architecture for customer organization accounts and multi-user access in ArtCRM.

It does not implement UI, customer organization backend, auth, invitations, email sending, email verification, domain verification, database schema, SQL, ORM, migrations, customer cabinet, organization roles enforcement, tests, dependencies, containers, `.env.example` changes, real customer data, real emails, credentials, tokens, secrets, or business logic.

## Purpose

A customer company may have multiple users: purchaser, engineer, approver, accountant, customer account administrator, and viewer. The marketplace portal needs a customer organization model so future carts, requests, quotes, documents, favorites, and repeated requests can be shared according to company policy.

The own-only MVP from [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md) remains the starting point. Organization sharing is future architecture, not implemented here.

Future customer organizations need their own roles and permissions because company users may have different responsibilities. Staff access to customer organization data must also be controlled separately by ArtCRM staff permissions and audit.

## MVP Vs Future Model

### MVP

- Customer sees only own carts/requests/history.
- No organization sharing unless explicitly implemented later.
- Backend ownership checks required.

### Future

- Customer organization can have multiple users.
- Carts/requests/quotes may be organization-owned.
- Organization admin may invite users.
- Users may have organization roles.
- Visibility can be own-only, team-shared, or organization-shared.

## Conceptual Entities

Conceptual objects only; no DB schema is created:

- `customer_organization`
- `customer_user`
- `customer_contact`
- `customer_membership`
- `customer_role`
- `customer_permission`
- `organization_invitation`
- `organization_domain_policy`
- `organization_audit_event`

## Customer Organization Fields

Conceptual fields:

- `customer_organization_id`
- `company_name`
- `inn`
- `kpp`
- `legal_name`
- `billing_details_ref`
- `delivery_addresses[]`
- `verified_domains[]`
- `status`
- `created_at`
- `audit_ref`

No real company data is included.

## Customer User Fields

Conceptual fields:

- `customer_user_id`
- `email`
- `display_name`
- `phone`
- `organization_memberships[]`
- `status`
- `created_at`
- `last_login_at`
- `audit_ref`

No real emails are included.

## Organization Roles

Future customer-side roles:

- `organization_admin`
- `purchaser`
- `engineer`
- `approver`
- `accountant`
- `viewer`

### Organization Admin

May:

- Invite users.
- Revoke users.
- Manage organization profile if allowed.
- See organization-shared carts/requests/quotes if policy allows.

### Purchaser

May:

- Create carts.
- Submit quote requests.
- View own and shared purchase-related history.

### Engineer

May:

- View catalog.
- Create technical selection drafts.
- Comment/attach technical specification if future feature allows.
- Require purchaser approval to submit if policy requires it.

### Approver

May:

- Approve request before sending to ArtCRM if future workflow allows.
- View quotes.
- Approve internal customer-side quote decisions.

### Accountant

May:

- View commercial documents if future policy allows.
- Access invoices/contracts if document center allows.

### Viewer

May:

- Read allowed organization objects only.

## Customer-Side Permissions

Conceptual permissions:

- `customer_org.view`
- `customer_org.edit_profile`
- `customer_org.invite_user`
- `customer_org.revoke_user`
- `customer_org.assign_role`
- `customer_cart.create`
- `customer_cart.view_own`
- `customer_cart.view_shared`
- `customer_cart.view_org`
- `customer_cart.submit`
- `customer_request.create`
- `customer_request.view_own`
- `customer_request.view_shared`
- `customer_request.view_org`
- `customer_quote.view_own`
- `customer_quote.view_shared`
- `customer_quote.view_org`
- `customer_quote.approve`
- `customer_documents.view`
- `customer_documents.upload`
- `customer_documents.download`
- `customer_audit.view_org`

## Invitation Lifecycle

Future invitation states:

- `invited`
- `pending_acceptance`
- `active`
- `suspended`
- `revoked`
- `expired`

Rules:

- Invitations are future implementation.
- Invitation email sending is deferred.
- Organization admin invitation flow is future.
- Staff-created invitation flow is future.
- Every invitation event must be auditable.

## Domain / Email Verification Boundary

Future boundary:

- Verified email domains.
- Domain-based membership suggestion.
- Email verification.
- Magic-link or code as future option.
- Domain policy must not auto-grant sensitive access without confirmation.
- Exact provider/method deferred.

## Ownership And Visibility

Visibility models:

- Own-only.
- Shared-by-user.
- Team/project shared.
- Organization-wide shared.

Rules:

- Customer cannot access another organization's data.
- Customer cannot enumerate organization IDs.
- Staff access requires ART-44 permissions.
- Guest has no organization access.
- Organization ownership must be enforced by backend later.

## Staff Support Access Boundary

Rules:

- Managers may view customer organization data only with relevant staff permissions.
- Support/admin access must be audited.
- Staff cannot impersonate customer silently.
- Future impersonation/support mode requires explicit audit and permission.
- Customer organization data must not be exposed to LLM agents unless workflow and permissions allow it.

## Audit Events

Future audit events:

- Organization created.
- Organization profile updated.
- User invited.
- Invitation accepted.
- Invitation expired.
- User added.
- User suspended.
- User revoked.
- Role assigned.
- Role removed.
- Permission changed.
- Cart shared.
- Request shared.
- Quote approved.
- Document viewed/downloaded.
- Staff support access.
- Access denied.

## Relationship To Marketplace Portal

Rules:

- Marketplace portal uses customer organization context after login.
- Organization context may affect visibility of carts/requests/quotes/favorites.
- Price visibility may later depend on organization policy.
- Saved items/favorites may be personal or organization-shared.
- Repeat previous request may be personal or organization-shared.
- Customer dashboard should later show organization context.

## Relationship To Other Docs

Related documents:

- [Customer Marketplace Portal](CUSTOMER_MARKETPLACE_PORTAL.md)
- [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md)
- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Internal CRM Communication Center](CRM_TASK_MESSENGER.md)

## Deferred Implementation

Explicitly deferred:

- UI.
- Customer organization backend.
- Auth.
- Invitations.
- Email verification.
- Domain verification.
- DB schema.
- SQL/ORM/migrations.
- Customer cabinet.
- Organization roles enforcement.
- Real customer data.

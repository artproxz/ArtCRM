# Customer Authentication and Guest Access

This document defines the documentation-only architecture for customer authentication and guest cart access in ArtCRM. It complements [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md) by detailing customer-facing catalog, cart, request, and authentication boundaries.

It does not implement frontend login UI, backend auth, auth middleware, email sending, OAuth, magic-link, email verification, database schema, SQL, ORM, migrations, rate limiting, payment, order placement, cart backend logic, new dependencies, containers, `.env.example` changes, real customer data, real emails, secrets, tokens, or production configuration.

## Purpose

ArtCRM needs a separate customer authentication and guest access document because customer-facing catalog and cart behavior has different risks from staff RBAC. Guests should be able to inspect public catalog information, but they must not create customer-owned data, submit requests, see private commercial data, or bypass ownership checks.

This document extends `SECURITY_RBAC_ARCHITECTURE.md` by focusing only on customer-facing states and transitions:

- Guest catalog browsing.
- Guest product-card viewing.
- Authentication required before add-to-cart.
- Authenticated customer cart and request ownership.
- Future email-based login and verification boundary.
- Session, rate-limiting, audit, privacy, and anti-abuse boundaries.

Customer data isolation is critical because carts, requests, contact information, attached files, commercial conditions, and request history must belong to the correct customer account or customer organization. Customer auth must be described before frontend/backend implementation so the future UI, backend, and persistence model do not accidentally treat frontend visibility as authorization.

## Scope

Covered here:

- Guest catalog browsing.
- Guest product card viewing.
- Auth requirement before add-to-cart.
- Authenticated customer cart.
- Guest-to-authenticated flow.
- Customer-owned carts and requests.
- Email-based login/verification as a future boundary.
- Session and rate limiting boundaries.
- Audit events.
- Privacy/data isolation.
- Abuse and scraping protection.

Not covered in detail:

- Staff RBAC; see [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md).
- Internal CRM messenger.
- Supplier quote flow.
- Price implementation.
- Real auth implementation.

## User States

### Guest

Guest is an unauthenticated visitor.

Guest can:

- Browse catalog.
- Search catalog.
- Open product cards.
- View public product-card information.

Guest cannot:

- Add item to cart.
- Save cart.
- Submit cart.
- Send request.
- Request commercial offer / KP.
- See request history.
- See personal conditions.
- See purchase prices.
- See supplier discounts.
- See internal comments.
- Upload files.
- Access customer-only data.

Important rule: to add any product to cart, authentication is required.

### Authenticated Customer

Authenticated customer can:

- Add products to cart.
- Save cart.
- Submit cart/request.
- Request commercial offer / KP.
- View own carts.
- View own requests.
- View own history.
- Update own profile/contact info if future UI allows.
- Attach files only if future policy allows.

Authenticated customer cannot:

- See other customers' carts or requests.
- See staff internal comments.
- See internal CRM messenger threads.
- See supplier quote responses.
- See purchase prices.
- See supplier discounts.
- See staff audit logs.
- Access manager-only functions.

### Staff Acting As Customer Support

Staff support access is separate from customer authentication:

- Staff may view customer carts/requests only with relevant permissions from `SECURITY_RBAC_ARCHITECTURE.md`.
- Staff support access must be audited.
- Staff support access does not make staff part of the customer auth flow.
- Customer-facing permissions must not be inferred from staff UI visibility.

## Guest Access Rules

Guest access is strictly read-only for public catalog and product-card data.

Rules:

- Guest cannot create persistent cart.
- Guest cannot add items to cart.
- Guest cannot request quote.
- Guest cannot submit request.
- Guest cannot upload files.
- Guest cannot see personalized price/discount terms.
- Guest browsing should be rate-limited conceptually to reduce scraping and abuse.
- Guest product-card data must exclude private, internal, and commercial fields.

## Add-To-Cart Authorization Boundary

Add-to-cart is the first protected customer action.

Rules:

- When guest clicks `Add to cart`, the system should require authentication.
- After authentication, add-to-cart can continue for the authenticated customer.
- Future UI may preserve the intended product/action during auth redirect, but no implementation is included in ART-45.
- No cart item should be persisted as a customer cart before authentication unless a future policy explicitly creates anonymous ephemeral session storage.
- If future anonymous session storage is used, it must be non-sensitive, short-lived, rate-limited, and not treated as customer-owned data until authentication.

Preferred MVP rule:

- No persistent guest cart.
- Authentication required before adding the first item.

## Guest-To-Authenticated Flow

Conceptual MVP flow:

1. Guest opens catalog.
2. Guest searches or filters product list.
3. Guest opens product card.
4. Guest clicks add-to-cart.
5. System prompts authentication.
6. Customer authenticates.
7. System creates or opens customer cart.
8. Product is added to authenticated customer cart.
9. Customer can continue cart/request workflow.

Alternative future flow:

- The system may create an optional short-lived intended action token.
- The system may redirect back to the product card after login.
- This token must not contain secrets, private prices, supplier discounts, purchase prices, or customer-owned data before authentication.
- No real implementation is added now.

## Customer Cart Ownership

Customer cart ownership rules:

- Every saved/submitted cart belongs to exactly one authenticated customer account or customer organization.
- Customer can see only own carts.
- Customer can see only own requests.
- Customer cannot access cart/request by guessing IDs.
- Backend authorization must check ownership on every customer cart/request operation.
- Frontend hiding is not enough.

## Customer Request Creation

Request creation rules:

- Submitting cart creates customer request / quote request.
- Request creation requires authenticated customer.
- Request must reference customer identity.
- Request submission should create an audit event.
- Request may later enter manager workflow.
- Customer does not receive internal manager-only fields.

## Email-Based Login / Verification Boundary

Future customer authentication options may include:

- Email/password.
- Email verification code.
- Magic link.
- OAuth-like email provider integration.
- Corporate/customer domain-based access.

Rules:

- Exact method is deferred.
- No email sending implementation in ART-45.
- No OAuth/magic-link implementation in ART-45.
- No provider choice in ART-45.
- Login events must be auditable in future.
- Email verification must protect against account takeover and unauthorized mailbox access.

## Customer Organization Model

Conceptual model only:

- Customer user may belong to customer organization/company.
- One customer organization may have multiple contacts/users in future.
- Carts/requests may belong to customer organization and be created by a specific customer user.
- Customer user visibility must be scoped by organization policy.
- For MVP, own-only visibility is acceptable until organization sharing rules are implemented.

This task does not add database schema.

## Public Vs Private Product-Card Fields

Guest-visible product card may include:

- Public name.
- Manufacturer.
- Product type.
- Basic public specifications.
- Public description.
- Public image if available.
- Approximate delivery label if policy allows.
- Public customer-facing price only if future policy allows.

Guest-hidden/internal fields:

- Purchase price.
- Supplier discount.
- Stock internals if not public.
- Supplier quote response.
- Internal analog rules.
- Internal matcher audit.
- Manager comments.
- Internal files.
- Margin.
- Manual discount rules.

## Rate Limiting And Anti-Abuse Boundaries

Conceptual controls:

- Guest catalog browsing limits.
- Search limits.
- Product-card open limits.
- Add-to-cart/auth-trigger limits.
- Login attempt throttling.
- Request submission limits.
- Per-IP limits.
- Per-session limits.
- Per-customer limits after login.
- Suspicious activity audit.
- Future WAF/CDN/proxy boundary from `SECURITY_RBAC_ARCHITECTURE.md`.

This task does not implement a rate limiter.

## Session Security

Customer session requirements:

- Customer session expiration.
- Logout.
- Session rotation after login.
- Session invalidation after password/auth reset.
- Session invalidation after account suspend/revoke.
- Secure cookie/token storage decision deferred.
- No tokens/secrets in logs.

## Audit Events

Future audit events:

- Guest product-card viewed if needed for abuse analytics.
- Auth prompt triggered by add-to-cart.
- Login success.
- Login failure.
- Logout.
- Cart created.
- Item added to cart.
- Item removed from cart.
- Cart submitted.
- Request created.
- Suspicious guest activity.
- Customer account suspended/revoked.
- Customer access denied due to ownership check.

## Privacy And Data Isolation

Rules:

- Customer sees only own carts, requests, and history.
- Customer cannot enumerate other customers' IDs.
- Staff access is controlled by ART-44 permissions.
- Service actors/agents require explicit permission.
- Internal messages and files are not customer-visible unless future workflow explicitly exposes them.
- Customer data must not be passed to LLM agents unless workflow and permissions allow it.

## Error And UX States

Conceptual states/messages:

- Guest tries to add to cart -> auth required.
- Customer session expired -> re-auth required.
- Customer tries to open another customer's cart -> access denied.
- Customer request submitted -> success state.
- Auth service unavailable -> retry/error state.
- Suspicious activity -> temporary restriction/challenge.

No UI implementation is included in this task.

## Relationship To Other Docs

Related existing documents:

- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Agent Platform](AGENT_PLATFORM.md)

Planned follow-up:

- `CRM_TASK_MESSENGER.md` is planned for ART-46.

## Deferred Implementation

The following work is explicitly deferred:

- Frontend login UI.
- Backend auth.
- Auth middleware.
- Customer user DB schema.
- Cart DB schema.
- SQL.
- ORM.
- Migrations.
- Email sending.
- Email verification code.
- Magic-link.
- OAuth/provider integration.
- Password reset.
- Rate limiter.
- WAF/CDN/proxy config.
- Customer profile UI.
- Organization sharing rules.
- Upload files.
- Payment/order placement.
- Production security config.

## Non-Goals For ART-SEC-002

This task does not add:

- Frontend UI.
- Backend auth.
- Middleware.
- Email sending.
- Magic-link/OAuth implementation.
- DB schema.
- SQL.
- ORM.
- Migrations.
- Tests.
- Dependencies.
- Containers.
- `.env.example` changes.
- Real customer data.
- Real emails.
- Credentials.
- Tokens.
- Secrets.
- Production config.
- Business logic.

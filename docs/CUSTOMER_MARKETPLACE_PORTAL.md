# Customer Marketplace Portal

This document defines the documentation-only architecture for the customer-facing ArtCRM marketplace-style KIP catalog portal.

It does not implement frontend UI, backend API, search engine, filters, sorting, cart logic, customer cabinet, file upload, parsing, OCR/Excel/PDF parsing, payment, order placement, database schema, SQL, ORM, migrations, tests, dependencies, containers, `.env.example` changes, real catalog data, real prices, real customer data, credentials, tokens, secrets, or business logic.

## Purpose

ArtCRM is not only an internal CRM for managers. It should also become a customer-facing marketplace-style portal for KIP and instrumentation products where customers can search, understand, compare, save, and request products.

The customer portal differs from internal CRM:

- Internal CRM is for staff workflows, request handling, matching, pricing, supplier quotes, commercial offers, and audit.
- Marketplace portal is for customer-facing catalog discovery, product understanding, cart/request creation, and customer history.
- Customer-visible data must be filtered by security and product-publication policies.

Customers need more than a raw list of products. A useful KIP catalog experience should help customers understand ranges, units, threads, accuracy classes, materials, compatible accessories, analog boundaries, and public documents.

The portal may rely on Product Selector and Catalog Matcher concepts, but it must not let LLM output independently confirm SKU, price, stock, delivery, or analog facts. Product Selector output is candidate data. Backend Catalog Matcher, catalog publications, validated analog/reference rules, and pricing/availability policies remain the source of truth.

This document builds on [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md): guest browsing is allowed, but persistent customer actions such as add-to-cart and request quote require authentication.

## User States

### Guest

Guest can:

- Browse catalog.
- Search catalog.
- Open product cards.
- View public product-card information.

Guest cannot:

- Add item to cart.
- Save cart.
- Submit request.
- Request commercial offer / KP.
- See personal conditions.
- See request history.
- See internal data.

MVP rule remains strict:

- No persistent guest cart.
- Add-to-cart requires authentication.

### Authenticated Customer

Authenticated customer can:

- Add items to cart.
- Save cart.
- Submit cart/request.
- Request commercial offer / KP.
- View own carts.
- View own requests.
- View own quote history.
- Use customer dashboard features.
- Access organization-shared data only when future organization policy allows it.

## Marketplace Catalog Experience

Future portal elements:

- Product listing page.
- Product card page.
- Customer-facing search.
- Filters.
- Sorting.
- Product comparison.
- Favorites/saved items.
- Related products/accessories.
- Analog candidates with strict validation boundary.
- Public document attachments such as certificates, passports, and manuals.
- Cart/request quote CTA after authentication.

No portal UI or search/filter engine is implemented in this task.

## Search And Filters

Future search/filter capabilities may include:

- Product type.
- Manufacturer.
- Series/model.
- Measuring range.
- Unit.
- Thread.
- Connection type.
- Accuracy class.
- Material.
- Execution.
- Output signal for sensors.
- Length/diameter for thermometers/thermowells.
- Availability/delivery estimate.
- Price visibility if policy allows.
- Related components/accessories.
- Analog availability if validated.

Important: this document does not implement search, filters, indexing, ranking, query parsing, or UI controls.

## Product Cards For KIP

Public product card may include:

- Public product name.
- Manufacturer.
- Product type.
- Series/model.
- Public technical characteristics.
- Range/unit/thread/accuracy/material if public.
- Public description.
- Related accessories.
- Compatible related components.
- Public documents: certificate, passport, manual.
- Approximate delivery label if policy allows.
- Public customer-facing price only if future policy allows.

Hidden/internal fields:

- Purchase price.
- Supplier discount.
- Margin.
- Manual discount rules.
- Internal matcher audit.
- Internal stock internals if not public.
- Supplier quote response.
- Internal comments.
- Internal files.
- Unvalidated analog rules.

## Product Comparison

Future comparison may allow customer-visible comparison of:

- Manufacturer.
- Model/series.
- Range.
- Unit.
- Thread.
- Connection type.
- Accuracy class.
- Material.
- Delivery estimate.
- Public price if allowed.
- Related accessories.
- Public documents.

Rules:

- Comparison must not expose internal fields.
- Comparison must not show unvalidated analogs as facts.
- Comparison is documentation-only for now.

## Favorites / Saved Items

Future behavior:

- Customer can save favorite items after authentication.
- Favorites belong to customer account or future customer organization.
- Favorites may be used to repeat requests.
- Guest favorites are not MVP unless future anonymous session policy is defined.

## Repeat Previous Request / Cart

Future behavior:

- Authenticated customer can repeat previous request/cart.
- Repeated cart must revalidate catalog items, availability, delivery estimate, and price visibility.
- Old prices, stock, and delivery labels must not be treated as current facts.
- Repeated request should display a `requires revalidation` boundary.

## Upload Specification / List

Future upload boundary:

- Customer may later upload Excel/PDF/Word/specification list.
- File upload requires authentication.
- Parsing/OCR/import is future functionality.
- Uploaded files must follow the file security boundary from [Internal CRM Communication Center](CRM_TASK_MESSENGER.md) and future document center architecture.
- LLM must not parse or interpret uploaded specification without explicit workflow and backend validation.

No file upload, parsing, OCR, or import implementation is included.

## Request Quote Flow From Cart

Conceptual flow:

- Add-to-cart requires authentication.
- Submitted cart creates customer request / quote request.
- Customer request enters staff pipeline later.
- Customer sees customer-facing status only.
- Manager internal workflow remains hidden.
- Quote lifecycle is planned for future `COMMERCIAL_OFFER_LIFECYCLE.md` / ART-49 if not yet created.

## Related Products And Accessories

Related products may include:

- Thermowells.
- Adapters.
- Valves.
- Siphon tubes.
- Seals.
- Hydrofilling service.
- Documents.
- Accessories.

Rules:

- Related suggestions must be validated by backend/catalog rules.
- LLM suggestions are candidate-only.
- No automatic unvalidated additions to cart/request.

## Analog Candidate Boundary

Rules:

- No unvalidated analogs shown as facts.
- Analogs require validated analog/reference layer.
- Product Selector and LLM may suggest intent/candidates only.
- Backend Catalog Matcher / analog rule layer must validate.
- If analog is not validated, show `needs_review` or ask manager/customer clarification.
- ART-35 analog reference remains a separate backlog area if relevant.

## Customer Dashboard

Future customer dashboard links:

- Active carts.
- Submitted requests.
- Quote history.
- Request status.
- Favorite items.
- Repeated requests.
- Organization-shared objects in future.
- Customer profile/company data in future.

No customer cabinet/dashboard implementation is included.

## Customer Catalog Assistant

Future customer catalog assistant boundary:

- Assistant may help ask questions and guide customer.
- Assistant may explain public product characteristics.
- Assistant may help collect intent.
- Assistant must not confirm exact SKU, price, stock, delivery, or analog as fact.
- Backend/Catalog Matcher remains source of truth.
- Assistant output must be auditable if used for request generation.

## Marketplace Abuse / Scraping Boundaries

Conceptual controls:

- Guest browsing rate limits.
- Search limits.
- Product-card open limits.
- Bot/scraping protections as future boundary.
- Add-to-cart requires authentication.
- Request submission limits.
- Suspicious activity audit.

No anti-abuse implementation is included in this task.

## Relationship To Other Docs

Related documents:

- [Customer Authentication and Guest Access](CUSTOMER_AUTH_AND_GUEST_ACCESS.md)
- [Security, RBAC and Access Control Architecture](SECURITY_RBAC_ARCHITECTURE.md)
- [Catalog Data Model](CATALOG_MODEL.md)
- [Backend Catalog Matcher Design](CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](CATALOG_MATCHER_API.md)
- [Catalog and Matcher Database Model](CATALOG_DATABASE_MODEL.md)
- [Product Selector Rulebook](PRODUCT_SELECTOR_RULEBOOK.md)
- [Product Selector Related Component Rules](PRODUCT_SELECTOR_RELATED_COMPONENTS.md)
- [Internal CRM Communication Center](CRM_TASK_MESSENGER.md)
- [Agent Platform](AGENT_PLATFORM.md)

## Deferred Implementation

Explicitly deferred:

- UI.
- Frontend catalog.
- Search engine.
- Filters.
- Sorting.
- Product comparison implementation.
- Favorites implementation.
- Cart implementation.
- Quote request implementation.
- Customer dashboard implementation.
- File upload.
- Parser/OCR.
- Payment/order placement.
- DB schema.
- Backend APIs.
- Real catalog data.
- Real prices.

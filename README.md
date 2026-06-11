# ArtCRM

Initial repository scaffold for ArtCRM.

This pilot setup intentionally does not include business logic. It only defines the first project structure and documentation placeholders needed for future implementation work.

## Repository Structure

- `backend/` - backend application placeholder.
- `frontend/` - frontend application placeholder.
- `infrastructure/` - deployment and infrastructure placeholder.
- `docs/` - project documentation placeholder.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Domain Model](docs/DOMAIN_MODEL.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Request Lifecycle](docs/REQUEST_LIFECYCLE.md)
- [Agent Platform](docs/AGENT_PLATFORM.md)
- [AgentRun Schema and Quality Policy](docs/AGENT_RUN.md)
- [Agent JSON Schemas and DTO Contracts](docs/AGENT_JSON_SCHEMAS.md)
- [Product Selector Evaluation Plan](docs/PRODUCT_SELECTOR_EVAL.md)
- [Product Selector Evaluation Fixtures](docs/PRODUCT_SELECTOR_FIXTURES.md)
- [Product Selector Evaluation Fixture JSON](docs/fixtures/product_selector_eval_fixtures.json)
- [Product Selector Rulebook](docs/PRODUCT_SELECTOR_RULEBOOK.md)
- [Product Selector Related Component Rules](docs/PRODUCT_SELECTOR_RELATED_COMPONENTS.md)
- [Catalog Data Model](docs/CATALOG_MODEL.md)
- [Catalog Source Mapping](docs/CATALOG_SOURCE_MAPPING.md)
- [ROSMA Catalog Import Plan](docs/ROSMA_CATALOG_IMPORT_PLAN.md)
- [Backend Catalog Matcher Design](docs/CATALOG_MATCHER.md)
- [Backend Catalog Matcher API Contract](docs/CATALOG_MATCHER_API.md)
- [Catalog and Matcher Database Model](docs/CATALOG_DATABASE_MODEL.md)
- [Security, RBAC and Access Control Architecture](docs/SECURITY_RBAC_ARCHITECTURE.md)
- [Customer Authentication and Guest Access](docs/CUSTOMER_AUTH_AND_GUEST_ACCESS.md)
- [Internal CRM Communication Center](docs/CRM_TASK_MESSENGER.md)
- [Customer Marketplace Portal](docs/CUSTOMER_MARKETPLACE_PORTAL.md)
- [Customer Organization Access](docs/CUSTOMER_ORGANIZATION_ACCESS.md)

## Backend Foundation

`backend/app/` contains placeholder module boundaries for catalog and matcher-related services: catalog, stock, pricing, delivery, supplier quotes, matcher, analogs, related components, and audit.

These modules contain DTO and service boundary placeholders only. They do not implement business logic, persistence, external calls, API routes, pricing, email sending, catalog import, matching algorithms, or integrations.

Backend boundary tests for these placeholders can be run with `python -m unittest discover`.

## Configuration

Copy `.env.example` to `.env` for local development configuration. The example file contains demo/dev-safe placeholder values only and must not be used as a real environment file with production secrets.

Do not commit real secrets, tokens, passwords, API keys, mail credentials, database credentials, or model paths. Local values belong in an untracked `.env` file.

Ollama is configured through `OLLAMA_BASE_URL` and model name variables such as `OLLAMA_MAIL_READER_MODEL` and `OLLAMA_CATALOG_MATCHER_MODEL`. ArtCRM does not configure Ollama through a filesystem path to a model file.

## Security Notes

- Never commit `.env` or environment-specific `.env.*` files.
- Keep `.env.example` committed with placeholder or demo values only.
- Never commit real tokens, passwords, API keys, mail credentials, database credentials, private keys, certificates, or model paths.
- Do not print secrets in logs, UI output, documentation examples, pull request descriptions, or issue comments.
- If a secret is accidentally committed, rotate it outside the repository and treat the repository value as compromised.
- Security architecture baseline is documented in [Security, RBAC and Access Control Architecture](docs/SECURITY_RBAC_ARCHITECTURE.md); implementation is deferred to later tasks.
- Customer auth and guest access architecture is documented in [Customer Authentication and Guest Access](docs/CUSTOMER_AUTH_AND_GUEST_ACCESS.md); implementation is deferred to later tasks.
- Internal CRM communication center, messenger, and attachments architecture is documented in [Internal CRM Communication Center](docs/CRM_TASK_MESSENGER.md); implementation is deferred to later tasks.
- Customer marketplace portal and customer organization access architecture are documented in [Customer Marketplace Portal](docs/CUSTOMER_MARKETPLACE_PORTAL.md) and [Customer Organization Access](docs/CUSTOMER_ORGANIZATION_ACCESS.md); implementation is deferred to later tasks.

## Development Workflow

- Linear is the source of tasks.
- GitHub pull requests are used to review changes.
- Codex works only on tasks with the `Ready for Codex` status.
- Use the real Linear issue ID to link a PR with Linear.
- Store the internal backlog code, such as `ART-001` or `ART-002`, additionally in the PR title and description.

## Development Architecture

Planned stack for future implementation:

- Frontend: React.
- Backend: FastAPI.
- Database: PostgreSQL.
- Cache/Queue: Redis.
- Local AI runtime: Ollama.
- Integration layer: backend-only boundary for mail, 1C, Ollama, catalog matching, and secrets.

Implementation of this stack is deferred to later tasks. This repository currently contains architecture documentation and backend boundary placeholders only.

## Current Scope

- Create the initial repository layout.
- Add project-level documentation placeholders.
- Avoid application logic, secrets, credentials, and production configuration.

## Assumption

This scaffold assumes runtime implementations, persistence, integrations, and deployment details are deferred to explicit future tasks.

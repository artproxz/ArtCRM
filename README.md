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

Implementation of this stack is deferred to later tasks. This repository currently contains architecture documentation only.

## Current Scope

- Create the initial repository layout.
- Add project-level documentation placeholders.
- Avoid application logic, secrets, credentials, and production configuration.

## Assumption

This scaffold assumes the project has not selected backend, frontend, infrastructure, or deployment technologies yet.

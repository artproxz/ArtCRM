# ArtCRM

Initial repository scaffold for ArtCRM.

This pilot setup intentionally does not include business logic. It only defines the first project structure and documentation placeholders needed for future implementation work.

## Repository Structure

- `backend/` - backend application placeholder.
- `frontend/` - frontend application placeholder.
- `infrastructure/` - deployment and infrastructure placeholder.
- `docs/` - project documentation placeholder.

## Configuration

Copy `.env.example` to `.env` for local configuration when implementation begins. The example file contains placeholder values only and must not be used as real credentials.

## Development Workflow

- Linear is the source of tasks.
- GitHub pull requests are used to review changes.
- Codex works only on tasks with the `Ready for Codex` status.
- Use the real Linear issue ID to link a PR with Linear.
- Store the internal backlog code, such as `ART-001` or `ART-002`, additionally in the PR title and description.

## Current Scope

- Create the initial repository layout.
- Add project-level documentation placeholders.
- Avoid application logic, secrets, credentials, and production configuration.

## Assumption

This scaffold assumes the project has not selected backend, frontend, infrastructure, or deployment technologies yet.

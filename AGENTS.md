# Agent Guidance

This repository is in its initial scaffold phase.

## Scope

- Keep changes minimal and issue-focused.
- Do not implement business logic until explicitly requested.
- Do not refactor unrelated files.
- Do not hardcode secrets, tokens, passwords, API keys, mail credentials, or model paths.
- Use placeholder values only in `.env.example`.

## Repository Areas

- `backend/` is reserved for backend application code.
- `frontend/` is reserved for frontend application code.
- `infrastructure/` is reserved for deployment and infrastructure assets.
- `docs/` is reserved for project documentation.

## Secret Handling Rules

- Never commit `.env` or environment-specific `.env.*` files.
- Keep `.env.example` committed with placeholder or demo values only.
- Never commit real tokens, passwords, API keys, mail credentials, database credentials, private keys, certificates, or model paths.
- Never print secrets in logs, UI output, documentation examples, pull request descriptions, or issue comments.
- If a real secret is found in the repository, stop work and report it so the secret can be rotated outside the codebase.

## Codex Workflow Rules

- Complete all tasks as small, reviewable pull requests.
- Never write directly to `main`.
- Branch names must include the real Linear issue ID and the internal backlog code.
- Example branch name: `codex/art-6-art-002-agents-md`.
- PR titles must include the real Linear issue ID and the internal backlog code.
- Example PR title: `ART-6 ART-002 — Add AGENTS.md rules`.
- PR descriptions must include `Implements ART-6` and `Internal backlog code: ART-002`.
- Do not use only the internal `ART-001` or `ART-002` code as a GitHub reference, because Linear links PRs by the real issue ID, for example `ART-5`.
- After completing work, always write the report in Russian.
- Reports must include changed files, what was implemented, checks performed, remaining risks, and the PR link.
- Do not add business logic, frameworks, dependencies, secrets, or integrations without a separate task.
- The frontend must not call Ollama, IMAP, 1C, databases, or secrets directly.
- All calls to Ollama, mail, 1C, and databases must go through the backend.
- All AI agent responses must be validated by the backend before being saved to business tables.

## Current Assumption

No application framework, runtime, database, deployment platform, or AI model provider has been selected yet.

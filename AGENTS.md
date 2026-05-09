# Repository Overview

> For domain terminology and concept definitions, see [DOMAIN_GLOSSARY.md](DOMAIN_GLOSSARY.md).

This repository contains a Python 3.12 CLI and a Flask + Vue 3 web application for organizing pair tennis tournaments. The CLI loads and validates participants, creates teams, optionally runs a group stage, builds a knockout bracket, assigns courts and time slots, and writes CSV/text outputs. The web application exposes the same tournament logic through a REST API with user authentication, people management, and a browser UI.

## High-Level Structure

### CLI (project root)

- `main.py` — CLI entry point that orchestrates input loading, team generation, optional group-stage flow, bracket generation, scheduling, and output writing.
- `models.py` — shared dataclasses and enums (`Participant`, `Team`, `Group`, `Match`, `PairingMode`) used by the CLI and the web backend.
- `io_utils.py` — participant CSV parsing/validation and output file generation.
- `pairing.py` — team creation rules, including pairing modes, fixed pairs, and balance logic.
- `grouping.py` — group creation, round-robin match generation, qualification, and group seeding rules.
- `bracket.py` — knockout bracket generation and group-to-bracket transition logic.
- `scheduling.py` — court and time-slot assignment for matches, including dependency-aware ordering.
- `run.py` — Flask application entry point (`python run.py` or `flask run`).
- `requirements.txt` — Flask backend runtime dependencies.
- `pyproject.toml` — project metadata and pytest configuration.

### Flask backend (`backend/`)

- `backend/__init__.py` — app factory: registers blueprints, initialises DB, creates uploads directory.
- `backend/config.py` — configuration class; reads `SECRET_KEY` and `DATABASE_URL` from environment.
- `backend/extensions.py` — SQLAlchemy singleton (`db`).
- `backend/models.py` — SQLAlchemy models: `User`, `Person`, `SortResult`. Separate from root `models.py`.
- `backend/auth.py` — `/api/auth` blueprint (signup, login, logout, me) and `login_required` decorator.
- `backend/api/__init__.py` — empty package marker.
- `backend/api/people.py` — `/api/people` blueprint: list, create (with photo upload), get, update rating, serve photo.
- `backend/api/sorting.py` — `/api/sorting` blueprint: run sorting, retrieve latest result.
- `backend/services/__init__.py` — empty package marker.
- `backend/services/sorting_service.py` — bridges DB `Person` objects to root `pairing.generate_teams()` for doubles; rating-descending sort for singles.

### Vue 3 frontend (`frontend/`)

- `frontend/package.json` — Vite + Vue 3 + vue-router + axios dependencies.
- `frontend/vite.config.js` — Vite config; dev server proxies `/api` to `http://localhost:5000`.
- `frontend/index.html` — HTML entry point.
- `frontend/src/main.js` — mounts Vue app with router.
- `frontend/src/App.vue` — root component with navigation bar shown to authenticated users.
- `frontend/src/router/index.js` — route definitions and navigation guard; unauthenticated users are redirected to `/login`; authenticated users with an incomplete profile are redirected to `/profile`.
- `frontend/src/services/api.js` — axios wrapper for all backend calls.

#### Frontend pages

| Route | View file | Access | Description |
|---|---|---|---|
| `/login` | `src/views/LoginView.vue` | Public | Email + password login form. Redirects to `/profile` if profile incomplete, otherwise to `/people`. |
| `/signup` | `src/views/SignUpView.vue` | Public | New account registration form. Always redirects to `/profile` after signup. |
| `/profile` | `src/views/ProfileView.vue` | Authenticated | View and edit profile: full name, username, skill level, gender. Email shown read-only. Required before accessing other pages. |
| `/people` | `src/views/PeopleView.vue` | Authenticated, profile complete | List of all people with inline rating editing. |
| `/people/new` | `src/views/PersonFormView.vue` | Authenticated, profile complete | Form to add a new person (name, skill, photo). |
| `/sorting` | `src/views/SortingView.vue` | Authenticated, profile complete | Mode selection (singles/doubles) and sort execution. |

### Tests (`tests/`)

- `tests/test_bracket.py` — knockout bracket logic.
- `tests/test_cli.py` — end-to-end CLI behavior.
- `tests/test_grouping.py` — group creation and round-robin generation.
- `tests/test_pairing.py` — team pairing modes and balance logic.
- `tests/test_scheduling.py` — court and time-slot assignment.
- `tests/test_sorting_service.py` — sorting service unit tests (singles, doubles, edge cases).
- `tests/test_api.py` — Flask API integration tests (auth, people, sorting).

### Docker

- `Dockerfile` — builds the Flask backend image.
- `frontend/Dockerfile` — builds and serves the Vue frontend via nginx.
- `docker-compose.yml` — composes backend + frontend services.

## Modification Guardrails

- Keep changes limited to the requested scope.
- Preserve existing behavior unless the requested change explicitly requires different behavior.
- Reuse existing patterns, models, and module boundaries before introducing new ones.
- Apply DRY and SOLID principles where they fit the current design.
- Avoid duplication, hidden coupling, and large unrelated refactoring.
- Check the existing implementation and test patterns before adding new APIs, names, or file layouts.
- Do not add new runtime dependencies, frameworks, or architectural layers without a clear repository-supported reason.
- Do not mix root `models.py` (CLI dataclasses) with `backend/models.py` (SQLAlchemy DB models).

## Dependent-Object Update Rules

- When changing shared models or enum values in `models.py`, update all affected modules, CLI handling, writers, and tests together.
- When changing CLI arguments in `main.py` or CSV/output handling in `io_utils.py`, also update the related CLI tests and `README.md`.
- When changing pairing behavior in `pairing.py`, verify downstream effects on grouping, bracket generation, summaries/outputs, `sorting_service.py`, and tests that depend on team composition or strength ordering.
- When changing group-stage behavior in `grouping.py`, also check bracket qualification/seeding in `bracket.py`, scheduling assumptions in `scheduling.py`, and the related tests.
- When changing knockout behavior in `bracket.py`, also verify inputs from grouping, scheduling expectations, and output formatting/tests.
- When changing scheduling behavior in `scheduling.py`, also review match output expectations and tests for court assignment, time slots, and dependency ordering.
- When changing Flask models in `backend/models.py`, update related API routes, service layer, and API tests together.
- When changing API routes or request/response shapes in `backend/api/`, update `frontend/src/services/api.js`, affected Vue views, and `tests/test_api.py` together.
- When adding a new major workflow or object, place it with the existing module that owns that responsibility and add/update focused tests and documentation where user-visible behavior changes.
- When removing or renaming CLI options, CSV fields, output columns, or output files, update dependent tests and documentation in the same change.
- When changing environment variables or Docker configuration, update `README.md` and `docker-compose.yml` together.

## Testing and Verification

- Use the existing test command for repository verification: `python -m pytest`.
- Keep verification proportional to the change; run targeted checks while iterating and the relevant full test suite before finishing.
- Add or update tests in `tests/` whenever behavior changes or new rules are introduced.
- API tests use an in-memory SQLite database via the Flask test client; do not depend on a running server.
- For documentation-only changes, verify that the documented commands, modules, and responsibilities still match the repository state and note any manual checks performed.

## Style and Documentation Rules

- Follow the existing Python 3.12 style, naming, and module organization already present in the repository.
- All Python files use `from __future__ import annotations`.
- Keep new code and documentation concise, factual, and behavior-focused.
- Extend existing modules and tests instead of creating parallel patterns for the same responsibility.
- Match the repository's current naming and folder conventions before introducing new structure.
- Keep comments and documentation short and useful; avoid narrative or marketing-style text.

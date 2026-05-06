# AGENTS.md

## Purpose

This file defines the architecture, conventions, and development rules
for Artemis.

Artemis is an AI-assisted job search and application copilot built as a
domain-driven modular monorepo. It is intentionally designed to start as
a modular monolith and later be split into services.

------------------------------------------------------------------------

# Core Principles

-   Prefer clarity over cleverness
-   Prefer explicit over implicit behavior
-   Prefer thin API layers
-   Prefer domain ownership of logic
-   Avoid premature optimization
-   Avoid premature microservices

------------------------------------------------------------------------

# Monorepo Structure

artemis-job-copilot/ ├── apps/ │ ├── web/ │ ├── api/ │ └── worker/ ├──
docs/ ├── packages/ ├── scripts/ ├── AGENTS.md ├── README.md ├──
docker-compose.yml ├── Makefile └── .env.example

------------------------------------------------------------------------

# Backend Architecture

apps/api/app/ ├── api/ │ └── routes/ ├── domains/ ├── integrations/ ├──
infrastructure/ └── common/

------------------------------------------------------------------------

# Domain Rules

Each domain must include: - models.py - schemas.py - repository.py -
service.py

------------------------------------------------------------------------

# Route Rules

Routes must: - validate input - call services - return responses

Routes must NOT: - contain business logic - query DB directly - handle
storage logic

------------------------------------------------------------------------

# Database Rules

-   Use SQLAlchemy
-   Use repository layer
-   Avoid cross-domain coupling

------------------------------------------------------------------------

# Naming Conventions

-   Files: snake_case
-   Classes: PascalCase
-   Functions: snake_case

------------------------------------------------------------------------

# Commenting Rules

Every file must include a short header comment explaining its purpose.

------------------------------------------------------------------------

# Security Rules

Current system is NOT production ready.

Required before production: - password hashing - JWT auth - route
protection - ownership checks

------------------------------------------------------------------------

# AI Rules

AI must NOT fabricate: - work authorization - experience - legal
eligibility

------------------------------------------------------------------------

# Extractability Rule

Code must remain modular and separable into services.

------------------------------------------------------------------------

# Current State

-   Backend scaffold complete
-   Resume upload working
-   Parser stub in place

------------------------------------------------------------------------

## File Size and Constant Extraction

- Prefer keeping files roughly in the **250–350 line range** when practical
- If a file grows too large, split it by responsibility rather than letting it become bloated
- Large keyword sets, regex patterns, static mappings, and configuration-like values should usually be extracted into a `constants.py` file within the relevant domain
- Any constant used in multiple files within the same domain must be defined in that domain's shared `constants.py` (or equivalent domain-level constants module), not duplicated across files
- Any constant used across multiple domains must be defined in a global shared domain constants module (for example `src/domain/constants.py`) and imported from there
- Avoid cluttering business-logic files with long constant declarations when those constants can live in a dedicated module
- Split by cohesion, not arbitrarily: related constants should stay near the domain they belong to

------------------------------------------------------------------------

## Testing Rules

- Use `pytest` for backend testing
- Add API tests under `apps/api/tests/api/`
- Add unit tests under `apps/api/tests/unit/`
- Prefer shared fixtures in `apps/api/tests/conftest.py`
- Use a dedicated test database configuration
- New backend features should generally include tests for:
  - service logic
  - API behavior
  - important parsing/normalization logic
- Prefer deterministic test inputs over brittle real-world documents when possible

------------------------------------------------------------------------

## Auth and Resource Scoping Rules

- Authenticated resource endpoints should prefer implicit user scoping over client-supplied user IDs
- Prefer:
  - `GET /profile`
  - `POST /profile`
  - `GET /resumes`
  - `POST /resumes/upload`
- Avoid requiring clients to send their own `user_id` for self-scoped resources
- Authentication logic belongs in `src/deps/auth.py`
- Authorization logic belongs in `src/deps/authorization.py` when ownership or role checks are needed

------------------------------------------------------------------------

## Resume Parsing Architecture

- All resume parsing logic must be modularized under:
  `src/domain/resume/extractors/`

- Each extractor should have a single responsibility:
  - `header.py` → name, title, contact info
  - `sections.py` → experience, education, skills
  - `dates.py` → date parsing and experience calculation
  - `links.py` → URL extraction and classification

- `normalizer.py` must act as an orchestrator only and should not contain heavy parsing logic

- Extractor files should remain under ~300 lines

------------------------------------------------------------------------

## Service and Helper Function Placement

- Keep service files focused on orchestration and business flow.
- Do not define general-purpose helper functions inside `service.py` files.
- Move reusable pure helper logic into a nearby `helpers.py` file within the same domain folder.
- Examples of helper logic that belong in `helpers.py`:
  - value resolution helpers
  - label / field parsing helpers
  - unresolved field filtering helpers
  - formatting / coercion helpers
- `service.py` methods may still contain small flow-specific logic, but reusable helper behavior should live outside the service file.

------------------------------------------------------------------------

## Storage Rules

- File storage is a shared cross-cutting concern, not a domain-specific one.
- The storage backend must be abstracted behind a `StorageService` protocol defined in `src/integrations/storage/base.py`.
- Backend selection (local vs S3) belongs in `src/integrations/storage/factory.py`.
- The active storage service must be injected as a FastAPI dependency from `src/deps/storage.py`, following the same pattern as `src/deps/auth.py`.
- Routes must never instantiate a storage service directly — they receive it via `Depends(get_storage)`.
- Domain services (e.g. `ResumeService`) receive the storage service as a constructor argument — they do not create it.
- Pure storage helpers (e.g. reading a stored file back, resolving a pre-signed URL) belong in `src/integrations/storage/helpers.py`, not in any domain service or storage backend class.
- This pattern applies to all future file uploads (resume files, profile pictures, cover letters, etc.).

------------------------------------------------------------------------

## Logging Rules

- All service files across every domain and subdomain must include meaningful logs.
- Service logs should capture important lifecycle events such as:
  - operation start
  - operation completion
  - key counts / summaries
  - notable failures
- Do not spam logs with every branch or every field-level action unless debugging a specific issue.
- Do not log sensitive payload contents, full profile objects, tokens, or large raw responses.
- Prefer concise, readable logs that make debugging easier.

------------------------------------------------------------------------

## Job Feed Integration Strategy

- Artemis derives its Greenhouse/Lever/Ashby adapter patterns from the open-source `career-ops` project.
- Additional context reference fork: https://github.com/kunle97/career-ops
- Before adding a new job source adapter in Artemis, check whether `career-ops` already supports that ATS and follow the same ingestion pattern when applicable.
- Keep `JOB_SOURCE_REGISTRY` in `src/domain/jobs/constants.py` aligned with the company source coverage in `career-ops/templates/portals.example.yml` when onboarding new companies.
- `career-ops` is not a runtime dependency of Artemis: adapter logic is ported to Python in this repository and must not be invoked via subprocess calls.

------------------------------------------------------------------------

## Frontend API Service Rules

- All frontend HTTP requests must use `axios`. Do not use `fetch` for API calls in `services/web`.
- Frontend API logic must live under `services/web/src/services/`.
- Organize frontend service modules by backend domain ownership, for example:
  - `src/services/auth/`
  - `src/services/applications/`
  - `src/services/profile/`
- Do not place API-calling logic in `src/app/lib/`.
- UI components and pages should call domain service functions, not inline HTTP logic.

------------------------------------------------------------------------

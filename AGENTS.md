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
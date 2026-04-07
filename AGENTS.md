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

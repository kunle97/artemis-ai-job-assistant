# Skill: AGENTS.md Compliance Guard

## Purpose

Use this skill to verify that the most recent repository changes comply with the rules in AGENTS.md before finalizing implementation.

## When To Use

Use this skill whenever:
- You changed backend code in services/api.
- You created or modified route, service, repository, schema, model, dependency, or integration files.
- You made architectural changes that may affect domain boundaries.
- You are preparing to mark a Jira task as complete.

## Required Inputs

- Path to AGENTS.md.
- Scope of recent changes to review:
  - Unstaged changes.
  - Staged changes.
  - Last commit (HEAD).

## Required Review Workflow

1. Read AGENTS.md fully before reviewing code changes.
2. Identify changed files from:
   - Unstaged diff.
   - Staged diff.
   - Last commit diff (HEAD~1..HEAD) when available.
3. Review each changed file only against relevant AGENTS.md rules.
4. Produce a compliance report with PASS, WARN, or FAIL per rule.
5. If any FAIL exists, propose exact file-level fixes and stop short of claiming completion.

## Compliance Checklist

### Architecture and Layering

- Route files:
  - Validate input.
  - Call services.
  - Return responses.
  - Do not contain business logic.
  - Do not query database directly.
  - Do not implement storage logic directly.
- Domain ownership:
  - Domain logic lives in domain service layer.
  - Repository handles persistence.
  - Integrations remain integration-specific.
- Extractability:
  - Changes remain modular and separable into future services.

### Domain Structure

For any touched domain, ensure expected files exist and are used correctly:
- models.py
- schemas.py
- repository.py
- service.py

### Naming and File Organization

- Files use snake_case.
- Classes use PascalCase.
- Functions use snake_case.
- Avoid bloated files when possible; split by responsibility if needed.

### Comments and Readability

- Every modified Python file starts with a short purpose header comment.
- Comments are concise and explain non-obvious logic only.

### Services and Helpers

- service.py focuses on orchestration and business flow.
- Reusable pure helpers are not embedded inside service.py.
- Shared helper logic is moved into helpers.py where appropriate.

### Storage Integration

- Storage logic is abstracted behind StorageService protocol.
- Service selection uses integrations/storage/factory.py.
- FastAPI dependency injection is used from deps/storage.py.
- Routes do not instantiate storage services directly.

### Auth and Resource Scoping

- Self-scoped endpoints do not require client-supplied user_id.
- Authentication concerns live in src/deps/auth.py.
- Authorization concerns live in src/deps/authorization.py when needed.

### Logging

- Service changes include meaningful lifecycle logs:
  - start
  - completion
  - key summary counts
  - notable failures
- Logs do not leak sensitive data.

### Security Baseline

For auth/security-related changes, confirm production-hardening expectations are respected:
- password hashing in place
- JWT auth and route protection present where required
- ownership checks where applicable
- no fabricated AI claims related to legal eligibility or work authorization

### Testing

- New backend behavior includes tests where applicable:
  - API tests in services/api/tests/api/
  - unit tests in services/api/tests/unit/
- Test coverage targets critical service logic and behavior changes.

## Required Output Format

Return this exact sectioned structure:

1. Summary
- Overall status: PASS, WARN, or FAIL
- Files reviewed
- Number of checks: passed, warned, failed

2. Findings (ordered by severity)
- [FAIL|WARN|PASS] Rule name
- File path(s)
- Evidence
- Required fix (for FAIL/WARN)

3. Decision
- Ready to proceed: Yes/No
- If No, list blocking fixes

## Guardrails

- Do not auto-approve if any rule clearly fails.
- Do not invent AGENTS.md rules that are not present.
- Be explicit and file-specific in all findings.

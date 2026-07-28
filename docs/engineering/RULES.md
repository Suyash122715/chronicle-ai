# Engineering Rules & Standards

> **Project:** Chronicle AI  
> **Version:** 1.0.0  
> **Status:** Active  
> **Owner:** Suyash Bro

---

# 1. Purpose

This document defines the engineering standards of Chronicle AI.

Every engineer and every AI coding agent must follow these rules.

If code conflicts with these rules, the code must be changed.

These rules are mandatory.

---

# 2. Engineering Philosophy

Chronicle AI is built as a production SaaS.

Every engineering decision should optimize for

- Maintainability
- Readability
- Scalability
- Security
- Testability

Never optimize for writing less code.

Optimize for writing better software.

---

# 3. General Principles

Always

- Keep code simple.
- Prefer readability.
- Prefer explicit code.
- Write self-documenting code.
- Think long term.

Never

- Write temporary hacks.
- Add unnecessary complexity.
- Introduce clever code that is difficult to understand.

---

# 4. SOLID Principles

Every module should follow SOLID.

- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

If uncertain,

choose Single Responsibility.

---

# 5. Clean Architecture

The project follows Clean Architecture.

Dependencies always point inward.

Presentation

↓

Application

↓

Domain

↓

Infrastructure

Business logic belongs only in the Application and Domain layers.

---

# 6. Backend Standards

Framework

FastAPI

Language

Python 3.13

Package Manager

uv

Validation

Pydantic v2

ORM

SQLAlchemy 2

Migration

Alembic

Never introduce another backend framework without discussion.

---

# 7. Frontend Standards

Framework

Next.js

Language

TypeScript

Routing

App Router

Styling

Tailwind CSS

Components

shadcn/ui

State Management

Zustand

Server State

TanStack Query

Validation

Zod

---

# 8. Database Rules

Database

PostgreSQL

Never query the database directly from API routes.

All persistence must go through repositories.

Every schema change requires an Alembic migration.

---

# 9. API Rules

REST only.

Version all APIs.

Example

/api/v1/artifacts

Every request must be validated.

Every response must be validated.

Never expose stack traces.

---

# 10. Naming Conventions

Files

snake_case

Python Classes

PascalCase

Functions

snake_case

Variables

snake_case

React Components

PascalCase

Constants

UPPER_CASE

Database Tables

plural

Database Columns

snake_case

---

# 11. Function Guidelines

One responsibility.

Prefer early returns.

Avoid nested conditions.

Target size

20–40 lines.

Refactor if significantly longer.

---

# 12. File Guidelines

Prefer files under 250 lines.

Split by responsibility rather than by size alone.

Avoid "god files."

---

# 13. Comments

Comment **why**, not **what**.

Bad

# increment counter

Good

# Retry count is limited to avoid infinite processing loops.

Remove commented-out code before committing.

---

# 14. Error Handling

Never swallow exceptions.

Never use bare except.

Raise meaningful exceptions.

Return user-friendly error messages.

Log unexpected failures.

---

# 15. Logging

Log

- Authentication
- Uploads
- AI Processing
- Warnings
- Errors

Never log

- Passwords
- JWT tokens
- API keys
- Personal secrets

---

# 16. Security

Never hardcode

- Secrets
- Passwords
- API Keys
- Database URLs

Always use environment variables.

Validate

- Inputs
- File types
- File size

---

# 17. Artifact Rules

Internally

Everything is an Artifact.

Never build features assuming only PDFs exist.

Support future artifact types by design.

---

# 18. AI Rules

AI is an external service.

AI must never

- Update the database directly.
- Delete files.
- Bypass business logic.
- Make authorization decisions.

AI returns structured information.

The application decides what to do.

---

# 19. Dependencies

Before adding a dependency ask

- Does Python/TypeScript already provide this?
- Is it actively maintained?
- Is it widely adopted?
- Does it introduce vendor lock-in?

If unsure,

ask first.

---

# 20. Testing

Business logic should be independently testable.

Avoid framework-dependent code inside domain logic.

Critical features require

- Unit Tests

Important workflows require

- Integration Tests

---

# 21. Documentation

Implementation is incomplete unless documentation is updated.

Update when necessary

- API.md
- MEMORY.md
- CHANGELOG.md
- ARCHITECTURE.md

Documentation is part of the feature.

---

# 22. Git Workflow

Branch Naming

feature/<feature-name>

bugfix/<bug-name>

hotfix/<bug-name>

Commit Format

feat:

fix:

docs:

refactor:

test:

chore:

Examples

feat: implement artifact upload

fix: resolve JWT refresh bug

docs: update database design

---

# 23. Pull Requests

Every PR must

- Build successfully
- Pass tests
- Update documentation
- Explain significant changes

No PR should contain unrelated changes.

---

# 24. Code Review Checklist

Review

- Architecture
- Naming
- Security
- Error Handling
- Performance
- Documentation
- Tests

---

# 25. Performance

Avoid

- N+1 queries
- Duplicate API calls
- Unnecessary rendering
- Premature optimization

Measure before optimizing.

---

# 26. Forbidden Practices

Do NOT

- Duplicate business logic.
- Hardcode configuration.
- Access the database from routers.
- Skip validation.
- Ignore exceptions.
- Commit secrets.
- Rewrite architecture without approval.
- Introduce frameworks without discussion.

---

# 27. Definition of Done

A task is complete only if

✓ Code compiles

✓ Lint passes

✓ Tests pass

✓ Documentation updated

✓ CHANGELOG updated

✓ MEMORY updated

✓ No known critical bugs

---

# 28. Engineering Motto

Build software that is easy to understand,

easy to test,

easy to maintain,

and easy to evolve.

Every line of code should make the project better than it was before.
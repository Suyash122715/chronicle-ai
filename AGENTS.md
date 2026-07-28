# AGENTS.md

# Chronicle AI - AI Agent Instructions

Version: 1.0

This file defines how every AI coding agent (Antigravity, Cursor, Claude Code, GitHub Copilot, Windsurf, etc.) must contribute to Chronicle AI.

These instructions are mandatory.

---

# Project Overview

Chronicle AI is an AI-powered Career Operating System.

It helps users organize, understand, connect and retrieve their academic and professional journey.

Chronicle AI is NOT

- a cloud storage application
- a Google Drive clone
- a LinkedIn clone
- a document manager

Chronicle AI IS

- an intelligent knowledge system
- a career memory
- a digital identity platform
- a personal knowledge graph

The goal is to transform uploaded artifacts into connected knowledge.

---

# Before Writing Any Code

Always read the following documents in order.

1. PROJECT_MANIFEST.md

2. docs/product/PRD.md

3. docs/engineering/ARCHITECTURE.md

4. docs/engineering/DATABASE.md

5. docs/engineering/API.md

6. docs/engineering/RULES.md

7. docs/management/PHASES.md

8. docs/management/MEMORY.md

If documentation conflicts with generated code,

DOCUMENTATION ALWAYS WINS.

Never rewrite documentation without permission.

---

# Project Philosophy

Architecture First.

Documentation First.

Implementation Second.

Never sacrifice architecture for speed.

Prefer maintainability over clever code.

Build for long-term scalability.

Every decision should support a future SaaS product.

---

# Technology Stack

## Frontend

- Next.js
- TypeScript
- App Router
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand

Do NOT introduce another frontend framework.

---

## Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic v2
- uv

Do NOT introduce Flask or Django.

---

## Database

PostgreSQL

Development only may use SQLite if explicitly requested.

---

## AI

Gemini (initial)

AI providers must remain replaceable.

Never tightly couple business logic with AI.

---

## Vector Database

Development

ChromaDB

Production

Qdrant

---

## Storage

Development

Local Storage

Production

Cloudflare R2

Storage implementation must remain replaceable.

---

# Architecture Rules

Follow Clean Architecture.

Business Logic must never depend on infrastructure.

Never place business logic inside

- routers
- controllers
- endpoints

Routers only receive requests.

Use cases perform business logic.

Repositories access databases.

Infrastructure talks to external services.

---

# Folder Rules

Never modify the repository structure.

Never create random folders.

Never create helper folders like

helpers/

misc/

temp/

random/

Everything must belong to an existing module.

---

# Naming Rules

Python

snake_case

Classes

PascalCase

React Components

PascalCase

Constants

UPPER_CASE

Variables

meaningful names

Never abbreviate unless universally understood.

Bad

usr

cfg

tmp

Good

user

configuration

temporary_file

---

# Code Style

Always

- use typing
- use docstrings where useful
- keep functions small
- prefer composition
- use dependency injection

Never

- create giant classes
- create giant functions
- duplicate logic
- hardcode values
- use magic numbers

---

# Function Rules

Every function should perform one task.

Prefer early returns.

Avoid nested logic.

Maximum function size

~40 lines

If longer

refactor.

---

# File Rules

Prefer

100–250 lines

Avoid

500+ line files

Split by responsibility.

---

# Error Handling

Never silently ignore errors.

Never use bare except.

Always provide meaningful exceptions.

Always log unexpected failures.

Never expose internal errors to users.

---

# Logging

Log

- uploads
- authentication
- AI processing
- warnings
- failures

Never log

- passwords
- secrets
- tokens
- API keys

---

# Security

Never hardcode

- passwords
- secrets
- JWT keys
- API keys

Always use environment variables.

Validate all inputs.

Validate uploaded files.

Assume user input is malicious.

---

# Database Rules

Never access the database directly from routers.

Repositories are the only layer allowed to query the database.

Never write raw SQL unless explicitly required.

Always create migrations.

---

# API Rules

Use REST.

Always version APIs.

Example

/api/v1/

Every response should follow

{
    "success": true,
    "message": "",
    "data": {},
    "meta": {}
}

Errors should follow

{
    "success": false,
    "message": "",
    "errors": []
}

---

# AI Rules

AI should never

- modify the database directly
- write files directly
- delete files
- decide business logic

AI returns structured information.

Application decides what to do.

---

# Artifact Philosophy

Internally

Everything is an Artifact.

Artifacts include

- PDFs
- DOCX
- Images
- GitHub repositories
- LinkedIn profiles
- Portfolio websites
- Research papers
- Certificates

Do not design around PDFs only.

---

# Performance

Avoid unnecessary database queries.

Avoid unnecessary API calls.

Paginate large datasets.

Cache expensive operations when appropriate.

Measure before optimizing.

---

# Dependencies

Before adding a dependency ask

Does Python already support this?

Can existing libraries solve it?

Is the dependency actively maintained?

Does it introduce vendor lock-in?

If unsure,

ask before adding it.

---

# Testing

Every important service should be testable.

Business logic should not depend on FastAPI.

Prefer dependency injection.

---

# Documentation

Whenever implementation changes,

update documentation.

Update

- MEMORY.md
- CHANGELOG.md

If architecture changes,

update

ARCHITECTURE.md

If APIs change,

update

API.md

Documentation is part of implementation.

---

# Git

Never generate commits automatically.

Never rewrite git history.

Never delete branches.

Never modify unrelated files.

---

# Quality Checklist

Before considering a task complete

✔ Code compiles

✔ No lint errors

✔ No type errors

✔ Documentation updated

✔ Memory updated

✔ Changelog updated

✔ Architecture respected

---

# If Requirements Are Unclear

Do NOT guess.

Do NOT invent features.

Do NOT assume architecture.

Instead

Explain what is unclear.

List possible approaches.

Ask for clarification.

---

# Things You Must Never Do

❌ Change folder structure

❌ Replace libraries

❌ Rewrite architecture

❌ Add unnecessary dependencies

❌ Ignore documentation

❌ Hardcode secrets

❌ Create duplicate code

❌ Mix business logic with API routes

❌ Access the database from controllers

❌ Skip validation

❌ Skip error handling

---

# Preferred Development Flow

Understand the task

↓

Read relevant documentation

↓

Explain the implementation plan

↓

Generate code

↓

Validate code

↓

Update documentation

↓

Stop

Never implement additional features that were not requested.

---

# Guiding Principle

Chronicle AI is being built as a production-quality SaaS.

Every line of code should improve maintainability, scalability, readability, and reliability.

When in doubt,

choose the simpler architecture.

When architecture and convenience conflict,

architecture wins.

When documentation and assumptions conflict,

documentation wins.

Quality is more important than speed.
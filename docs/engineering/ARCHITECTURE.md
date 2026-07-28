# Software Architecture Document

> **Project:** Chronicle AI  
> **Version:** 1.0.0  
> **Status:** Draft  
> **Owner:** Suyash Bro  
> **Last Updated:** July 2026

---

# 1. Purpose

This document defines the complete technical architecture of Chronicle AI.

It acts as the engineering blueprint for the project.

Every implementation must follow this architecture.

---

# 2. Architecture Goals

The architecture should be

- Modular
- Scalable
- Maintainable
- Secure
- Replaceable
- Testable

The application should scale without requiring architectural redesign.

---

# 3. High-Level Architecture

```

Browser

↓

Next.js Frontend

↓

REST API

↓

FastAPI Backend

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer

↓

PostgreSQL
Cloud Storage
Vector Database
AI Provider

```

---

# 4. Architectural Principles

## Separation of Concerns

Every layer has one responsibility.

Presentation

↓

Application

↓

Domain

↓

Infrastructure

Business logic must never depend on infrastructure.

---

## Dependency Rule

Dependencies always point inward.

Infrastructure depends on Domain.

Presentation depends on Application.

Domain depends on nothing.

---

## Replaceability

Every external service should be replaceable.

Examples

Gemini

↓

OpenAI

↓

Claude

↓

Local LLM

without rewriting business logic.

---

## Scalability

The application should support

1

↓

100

↓

10,000

↓

1,000,000

users through infrastructure changes, not architectural changes.

---

# 5. Core Components

## Frontend

Responsibilities

- User Interface
- Authentication UI
- Dashboard
- Upload
- Search
- Timeline
- Knowledge Graph

Technology

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand

---

## Backend

Responsibilities

- API
- Authentication
- Business Logic
- Artifact Processing
- AI Orchestration
- Search
- Timeline
- Knowledge Graph

Technology

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

---

## Database

Responsibilities

Store

- Users
- Artifacts
- Metadata
- Relationships
- Timeline
- Activity

Technology

PostgreSQL

---

## AI Layer

Responsibilities

- OCR
- Classification
- Entity Extraction
- Summarization
- Relationship Detection
- Embedding Generation

AI must never modify business data directly.

---

## Storage

Development

Local Storage

Production

Cloudflare R2

Storage must be abstracted behind an interface.

---

## Vector Database

Development

ChromaDB

Production

Qdrant

Only embeddings should be stored.

---

# 6. Clean Architecture

```

Presentation

↓

Application

↓

Domain

↓

Infrastructure

```

---

## Presentation Layer

Contains

- API Routes
- Request Validation
- Response Serialization

Must never contain business logic.

---

## Application Layer

Contains

Use Cases

Examples

Upload Artifact

Delete Artifact

Generate Timeline

Search Knowledge

---

## Domain Layer

Contains

Business Rules

Entities

Interfaces

Policies

No framework-specific code.

---

## Infrastructure Layer

Contains

Database

Storage

AI Providers

External APIs

---

# 7. Request Flow

```

Browser

↓

API Route

↓

Application Use Case

↓

Repository

↓

Database

↓

Response

```

Business logic exists only inside Use Cases.

---

# 8. AI Processing Flow

```

Artifact Upload

↓

Store Original

↓

Extract Text

↓

Classify Artifact

↓

Extract Entities

↓

Generate Summary

↓

Detect Relationships

↓

Generate Embeddings

↓

Store Metadata

↓

Ready

```

---

# 9. Search Flow

```

User Query

↓

Intent Detection

↓

Metadata Search

+

Semantic Search

+

Knowledge Graph Search

↓

Ranking

↓

Response

```

---

# 10. Timeline Flow

```

Artifacts

↓

Extract Dates

↓

Sort Events

↓

Merge Timeline

↓

Generate Career Journey

```

---

# 11. Knowledge Graph

Nodes

- User
- Artifact
- Skill
- Project
- Company
- Technology
- Certificate
- Achievement

Relationships

- CREATED
- USES
- LEARNED
- RELATED_TO
- CERTIFIED_IN
- WORKED_AT

---

# 12. Folder Structure

Repository

```

backend/

frontend/

docs/

docker/

infra/

scripts/

storage/

tools/

```

---

Backend

```

app/

application/

domain/

infrastructure/

presentation/

tests/

```

---

# 13. Security

Authentication

JWT

Passwords

bcrypt

Validation

Pydantic

Authorization

Role-Based

Every request must be validated.

---

# 14. Error Handling

Every exception should

- Be logged
- Return meaningful responses
- Never expose internal implementation

---

# 15. Logging

Log

- Uploads
- Authentication
- AI Processing
- Errors

Never log

- Passwords
- Tokens
- Secrets

---

# 16. Performance

Goals

API

<300ms

Search

<2s

Upload

<5s

Dashboard

<1s

---

# 17. Deployment Architecture

Development

```

Next.js

↓

FastAPI

↓

PostgreSQL

↓

Local Storage

↓

ChromaDB

```

Production

```

CDN

↓

Next.js

↓

FastAPI

↓

PostgreSQL

↓

Cloudflare R2

↓

Qdrant

```

---

# 18. Future Scaling

Phase 1

Single Instance

↓

Phase 2

Docker

↓

Phase 3

Background Workers

↓

Phase 4

Redis

↓

Phase 5

Load Balancer

↓

Phase 6

Multiple API Instances

↓

Phase 7

Kubernetes

---

# 19. Engineering Principles

- Architecture before implementation
- Documentation before code
- Replaceability over convenience
- Simplicity over cleverness
- Security by default
- Performance by design

---

# 20. Architecture Decision Policy

Any significant architectural change requires

- ADR
- Documentation update
- Team approval

Architecture must evolve intentionally.

---

# 21. Definition of Done

A feature is complete only if

- Code implemented
- Tests passing
- Documentation updated
- API documented
- CHANGELOG updated
- MEMORY updated

---

# 22. Final Statement

Chronicle AI is designed as a long-term platform.

The architecture should survive changes in frameworks, AI providers, databases, and infrastructure.

Business logic remains constant.

Everything else should be replaceable.
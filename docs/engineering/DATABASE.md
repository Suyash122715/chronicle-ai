# Database Design Document

> **Project:** Chronicle AI  
> **Version:** 1.0.0  
> **Status:** Draft  
> **Owner:** Suyash Bro  
> **Last Updated:** July 2026

---

# 1. Purpose

This document defines the logical and physical database design of Chronicle AI.

The database is the single source of truth for all user information.

The database stores structured knowledge.

AI providers may change.

Storage providers may change.

Frontend frameworks may change.

The database model should remain stable.

---

# 2. Database Philosophy

Chronicle AI is built around one central concept:

**Artifact**

Everything uploaded or connected by the user is considered an Artifact.

Examples

- Resume
- Certificate
- Project Report
- Internship Letter
- GitHub Repository
- Portfolio Website
- Research Paper
- Technical Blog
- LinkedIn Profile

Artifacts become knowledge.

Knowledge becomes relationships.

Relationships become intelligence.

---

# 3. Database Principles

- Every table uses UUIDs.
- Every table includes timestamps.
- Soft delete wherever possible.
- No duplicated information.
- Normalize core data.
- Denormalize only for performance when necessary.
- Never store AI-generated text without linking it to the originating artifact.

---

# 4. Core Entities

The system revolves around these entities.

```
User
│
├── Artifact
│     ├── Artifact Version
│     ├── Metadata
│     ├── Entity
│     └── Embedding
│
├── Timeline Event
│
├── Skill
│
├── Project
│
├── Achievement
│
└── Relationship
```

---

# 5. Users

Represents registered users.

Fields

- id
- email
- username
- password_hash
- full_name
- avatar_url
- created_at
- updated_at
- deleted_at

---

# 6. Artifacts

Every uploaded or connected resource.

Fields

- id
- user_id
- title
- artifact_type
- source
- original_filename
- stored_filename
- mime_type
- size
- storage_provider
- upload_status
- created_at
- updated_at
- deleted_at

Artifact Types

- Resume
- Certificate
- Project
- Internship
- Research
- Blog
- Portfolio
- GitHub
- LinkedIn
- Other

Upload Status

- Uploaded
- Processing
- Ready
- Failed
- Deleted

---

# 7. Artifact Versions

Allows version history.

Fields

- id
- artifact_id
- version_number
- storage_path
- created_at

Example

Resume

v1

v2

v3

Users can always restore previous versions.

---

# 8. Metadata

Generated after AI processing.

Fields

- id
- artifact_id
- language
- summary
- category
- confidence_score
- processed_at

Metadata never replaces the original artifact.

---

# 9. Entities

Extracted knowledge.

Examples

Python

TensorFlow

Google

Machine Learning

BMSIT

Fields

- id
- artifact_id
- entity_type
- entity_name
- confidence

---

# 10. Relationships

Stores AI-discovered relationships.

Example

Python

USED_IN

Fake News Detector

Fields

- id
- source_entity_id
- target_entity_id
- relationship_type
- confidence

Relationship Types

- USED_IN
- LEARNED_FROM
- CREATED_AT
- RELATED_TO
- CERTIFIED_IN
- WORKED_AT

---

# 11. Skills

Represents inferred and verified skills.

Fields

- id
- user_id
- name
- proficiency_level
- source
- verified

Sources

- Certificate
- Project
- Internship
- Manual

---

# 12. Projects

Fields

- id
- user_id
- title
- description
- github_url
- start_date
- end_date

Projects can be linked to

Skills

Artifacts

Technologies

Timeline

---

# 13. Certifications

Fields

- id
- user_id
- issuer
- certificate_name
- issue_date
- expiry_date
- credential_id

---

# 14. Timeline Events

Represents career milestones.

Fields

- id
- user_id
- title
- description
- event_date
- source_artifact_id
- importance

---

# 15. Embeddings

Stores vector references.

Fields

- id
- artifact_id
- chunk_index
- vector_id

Vectors remain in the vector database.

PostgreSQL stores references only.

---

# 16. Upload Jobs

Tracks AI processing.

Fields

- id
- artifact_id
- status
- started_at
- completed_at
- error_message

---

# 17. Activity Logs

Audit trail.

Examples

- Login
- Upload
- Delete
- Search
- Download
- Update

Fields

- id
- user_id
- activity_type
- created_at

---

# 18. Notifications

Future feature.

Examples

- Artifact processed
- New AI insight
- Resume outdated
- Storage warning

---

# 19. Indexing Strategy

Indexes

- email
- username
- artifact_type
- user_id
- created_at
- upload_status

Composite indexes should be added after performance analysis.

---

# 20. Naming Conventions

Tables

Plural

users

artifacts

projects

Columns

snake_case

Foreign Keys

user_id

artifact_id

project_id

---

# 21. UUID Strategy

Every table uses UUID.

Reasons

- Better for distributed systems.
- No predictable IDs.
- Easier future scaling.

---

# 22. Soft Delete

Every user-owned resource supports soft deletion.

deleted_at = NULL

means active.

Deleted records remain recoverable until permanently removed.

---

# 23. Future Tables

Possible future additions

- organizations
- recruiters
- teams
- shared_artifacts
- resume_templates
- ai_conversations

These are intentionally excluded from Version 1.

---

# 24. Database Rules

Never store passwords in plain text.

Never store embeddings in PostgreSQL.

Never allow direct table access from API routes.

All database access must go through repositories.

---

# 25. Final Statement

The database models a person's professional knowledge—not just their files.

It is designed to remain stable while AI providers, storage providers, and application features evolve.
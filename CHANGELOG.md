# Changelog

All notable changes to Chronicle AI will be documented here.

This project follows Semantic Versioning.

---

## [0.4.5] - Extraction Framework & Resume Extractor (Phase 4.5 Batch 2)

### Added

- Concrete `ResumeExtractor` implementation extending `BaseLLMExtractor`
- Refined resume prompt (`v1.md`) and JSON schema (`schema.json`)
- Pipeline integration connecting `ProcessArtifactUseCase` to `ExtractorExecutionService` post-classification
- Graceful exception handling for LLM provider failures during background artifact processing
- Unit and pipeline integration test coverage for `ResumeExtractor` and `ProcessArtifactUseCase`

---

## [0.1.0] - Planning

### Added

- Backend foundation with FastAPI health, authentication, and artifact workflows
- Immutable provenance value object for AI-derived domain values
- Repository structure
- Documentation architecture
- Project Manifest
- PRD
- Software Architecture
- Database Design
- Engineering Rules
- API Standards
- AGENTS.md
- Development Roadmap
- Project Memory

---

## Upcoming

- Additional document extractors (Certificate, Marksheet, Internship, Project, Portfolio, GitHub)
- Frontend Foundation
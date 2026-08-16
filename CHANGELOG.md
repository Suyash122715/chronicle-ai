# Changelog

All notable changes to Chronicle AI will be documented here.

This project follows Semantic Versioning.

---

## [0.5.0] - Complete Extraction Pipeline with Retrieval API (Phase 4.5 Complete)

### Added

- All 7 concrete document extractors implemented: `ResumeExtractor`, `CertificateExtractor`, `MarksheetExtractor`, `InternshipLetterExtractor`, `ProjectReportExtractor`, `PortfolioExtractor`, and `GitHubRepositoryExtractor`.
- Full `ExtractionResult` status enum: `SUCCESS`, `PARTIAL`, `FAILED`, `NOT_SUPPORTED`, `SKIPPED`.
- DB persistence for extraction results via `artifact_extractions` table (Alembic migration 004), `ArtifactExtractionModel`, `ExtractionRepositoryInterface`, and `SQLAlchemyExtractionRepository`.
- Pipeline persistence wired end-to-end through `ProcessArtifactUseCase`.
- Extraction retrieval API: `GET /api/v1/artifacts/{artifact_id}/extraction` — returns `structured_data`, `provenance`, `warnings`, `confidence`, `status`, `extractor_version`, `prompt_version`, `llm_metadata`, `started_at`, `completed_at`, `error_message`.
- Authentication and ownership protection enforced on the extraction endpoint.
- Complete dependency injection wiring connecting `ExtractorRegistry`, `ExtractorFactory`, `ExtractorExecutionService`, and `ProcessArtifactUseCase`.
- 187 backend tests passing with 2 pre-existing warnings.

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

- Phase 5: Knowledge Graph architecture, entity models, domain relationships, and graph persistence
- Frontend Foundation
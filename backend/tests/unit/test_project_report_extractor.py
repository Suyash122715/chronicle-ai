"""Unit tests for ProjectReportExtractor with mocked LLM provider."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.services.extractor_factory import ExtractorFactory
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.llm_response import LLMResponse
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.project_report_extractor import ProjectReportExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider returning canned project report extraction responses."""

    def __init__(
        self,
        canned_json: dict[str, Any] | None = None,
        raise_error: bool = False,
        is_disabled: bool = False,
    ) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "project_info": {
                "title": "ChronicleAI — Professional Document Intelligence Platform",
                "description": "A full-stack AI platform that extracts structured data from professional documents using Gemini LLM and presents a unified career knowledge graph.",
                "domain": "AI / Machine Learning",
                "team_name": "Chronicle Engineering",
                "start_date": "2024-01-15",
                "end_date": "2025-06-30",
                "github_url": "https://github.com/example/chronicle-ai",
                "demo_url": "https://chronicle.ai",
                "objective": "Build an automated professional profile from uploaded documents using LLM extraction.",
            },
            "authors": [
                {"name": "Alice Johnson", "role": "Lead Developer"},
                {"name": "Bob Smith", "role": "ML Engineer"},
            ],
            "technologies": [
                {"name": "Python", "category": "Programming Language"},
                {"name": "FastAPI", "category": "Framework"},
                {"name": "PostgreSQL", "category": "Database"},
                {"name": "Google Gemini", "category": "LLM"},
                {"name": "Next.js", "category": "Frontend Framework"},
            ],
            "outcomes": [
                "Achieved 95% extraction accuracy on benchmark dataset of 1,000 documents.",
                "Reduced manual profile setup time from 2 hours to under 5 minutes.",
                "Deployed to production handling 500+ daily users.",
            ],
            "skills": [
                {"name": "LLM Integration", "category": "AI"},
                {"name": "REST API Design", "category": "Backend"},
                {"name": "PostgreSQL", "category": "Database"},
            ],
            "_provenance": {
                "title": "Title on cover page: ChronicleAI — Professional Document Intelligence Platform",
                "domain": "Section header: AI / Machine Learning Project",
                "github_url": "Footer: Source code available at https://github.com/example/chronicle-ai",
            },
        }
        self.raise_error = raise_error
        self.is_disabled = is_disabled

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        if self.raise_error:
            raise RuntimeError("LLM provider mock error during project report extraction")

        if self.is_disabled:
            return LLMResponse(
                raw_response="",
                parsed_json=None,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency=0.0,
                provider="disabled",
                model="none",
                finish_reason="NO_API_KEY",
                prompt_version=prompt_version,
                metadata={"warning": "GEMINI_API_KEY is not configured."},
            )

        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 300, "completion_tokens": 150, "total_tokens": 450},
            latency=0.55,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "ChronicleAI Project Report — AI Platform for Document Intelligence") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="project_report.pdf",
        stored_filename="stored_project_report.pdf",
        file_path="storage/project_report.pdf",
        mime_type="application/pdf",
        file_size=8192,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.project_report(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_project_report_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for project report artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data
    info = data["project_info"]
    assert info["title"] == "ChronicleAI — Professional Document Intelligence Platform"
    assert info["domain"] == "AI / Machine Learning"
    assert info["github_url"] == "https://github.com/example/chronicle-ai"
    assert info["start_date"] == "2024-01-15"
    assert info["end_date"] == "2025-06-30"
    assert len(data["authors"]) == 2
    assert data["authors"][0]["name"] == "Alice Johnson"
    assert data["authors"][0]["role"] == "Lead Developer"
    assert len(data["technologies"]) == 5
    assert data["technologies"][0]["name"] == "Python"
    assert len(data["outcomes"]) == 3
    assert len(data["skills"]) == 3


@pytest.mark.asyncio
async def test_project_report_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_project_report_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped from _provenance."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "title" in result.provenance
    assert "ChronicleAI" in result.provenance["title"].evidence_snippet
    assert result.provenance["title"].artifact_id == artifact.id

    assert "domain" in result.provenance
    assert "AI / Machine Learning" in result.provenance["domain"].evidence_snippet

    assert "github_url" in result.provenance
    assert "github.com" in result.provenance["github_url"].evidence_snippet


@pytest.mark.asyncio
async def test_project_report_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert result.error_message is not None
    assert "LLM provider mock error during project report extraction" in result.error_message
    assert len(result.warnings) > 0
    assert "Extraction failed" in result.warnings[0]


@pytest.mark.asyncio
async def test_project_report_extractor_disabled_provider_returns_skipped() -> None:
    """Verifies missing API key (disabled provider) returns ExtractionStatus.SKIPPED, never SUCCESS."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(is_disabled=True)

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SKIPPED
    assert result.error_message == "GEMINI_API_KEY is not configured."
    assert any("GEMINI_API_KEY is not configured" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_project_report_extractor_registry_resolution() -> None:
    """Verifies ProjectReportExtractor registration and lookup via ExtractorRegistry."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.PROJECT_REPORT, extractor_instance)
    resolved = registry.get_extractor(DocumentType.project_report())

    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_project_report_extractor_factory_resolution() -> None:
    """Verifies ProjectReportExtractor resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.PROJECT_REPORT, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.project_report())
    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_project_report_extractor_string_technology_normalisation() -> None:
    """Verifies that a flat string list in 'technologies' is normalised to dicts."""
    flat_json: dict[str, Any] = {
        "project_info": {
            "title": "Flat Tech Project",
            "description": "A project with flat string technologies.",
        },
        "technologies": ["Python", "Docker", "Redis"],
        "authors": [],
        "outcomes": [],
        "skills": [],
        "_provenance": {
            "title": "Title: Flat Tech Project",
        },
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=flat_json)

    extractor = ProjectReportExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    techs = result.structured_data["technologies"]
    assert len(techs) == 3
    # Each string should be normalised into {"name": ..., "category": ""}
    assert all(isinstance(t, dict) for t in techs)
    assert techs[0]["name"] == "Python"
    assert techs[0]["category"] == ""

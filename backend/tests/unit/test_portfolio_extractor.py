"""Unit tests for PortfolioExtractor with mocked LLM provider."""

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
from app.infrastructure.ai.portfolio_extractor import PortfolioExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider returning canned portfolio extraction responses."""

    def __init__(
        self,
        canned_json: dict[str, Any] | None = None,
        raise_error: bool = False,
        is_disabled: bool = False,
    ) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "owner_info": {
                "name": "Jane Smith",
                "title": "Full Stack Developer & ML Engineer",
                "bio": "Passionate developer with 5 years of experience building scalable web applications and AI-powered systems.",
                "email": "jane.smith@example.com",
                "phone": "+91-9876543210",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "github_url": "https://github.com/janesmith",
                "website_url": "https://janesmith.dev",
            },
            "projects": [
                {
                    "title": "ChronicleAI",
                    "description": "AI-powered professional document intelligence platform.",
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "Google Gemini"],
                    "github_url": "https://github.com/janesmith/chronicle-ai",
                    "demo_url": "https://chronicle.ai",
                    "start_date": "2024-01-01",
                    "end_date": "2025-06-30",
                },
                {
                    "title": "Fake News Detector",
                    "description": "NLP model to detect fake news articles with 92% accuracy.",
                    "technologies": ["Python", "TensorFlow", "BERT"],
                    "github_url": "https://github.com/janesmith/fakenews",
                    "demo_url": "",
                    "start_date": "2023-05-01",
                    "end_date": "2023-09-30",
                },
            ],
            "skills": [
                {"name": "Python", "category": "Programming Language"},
                {"name": "FastAPI", "category": "Framework"},
                {"name": "PostgreSQL", "category": "Database"},
                {"name": "TensorFlow", "category": "ML Framework"},
            ],
            "work_experience": [
                {
                    "company": "TechCorp Solutions",
                    "role": "Software Engineering Intern",
                    "start_date": "2023-06-01",
                    "end_date": "2023-11-30",
                    "description": "Built REST APIs and optimized database queries.",
                },
            ],
            "education": [
                {
                    "institution": "Stanford University",
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "start_date": "2020-08-01",
                    "end_date": "2024-05-31",
                },
            ],
            "certifications": [
                "Google Professional Cloud Architect",
                "AWS Certified Solutions Architect",
            ],
            "_provenance": {
                "owner_name": "Header: Jane Smith — Full Stack Developer",
                "projects": "Section: Featured Projects — 2 entries listed",
                "skills": "Section: Skills — Python, FastAPI, PostgreSQL, TensorFlow listed",
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
            raise RuntimeError("LLM provider mock error during portfolio extraction")

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
            token_usage={"prompt_tokens": 350, "completion_tokens": 180, "total_tokens": 530},
            latency=0.48,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "Jane Smith — Full Stack Developer Portfolio") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="portfolio.pdf",
        stored_filename="stored_portfolio.pdf",
        file_path="storage/portfolio.pdf",
        mime_type="application/pdf",
        file_size=5120,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.portfolio(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_portfolio_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for portfolio artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data

    owner = data["owner_info"]
    assert owner["name"] == "Jane Smith"
    assert owner["title"] == "Full Stack Developer & ML Engineer"
    assert owner["email"] == "jane.smith@example.com"
    assert owner["github_url"] == "https://github.com/janesmith"
    assert owner["website_url"] == "https://janesmith.dev"

    assert len(data["projects"]) == 2
    assert data["projects"][0]["title"] == "ChronicleAI"
    assert "Python" in data["projects"][0]["technologies"]

    assert len(data["skills"]) == 4
    assert data["skills"][0]["name"] == "Python"

    assert len(data["work_experience"]) == 1
    assert data["work_experience"][0]["company"] == "TechCorp Solutions"

    assert len(data["education"]) == 1
    assert data["education"][0]["institution"] == "Stanford University"

    assert len(data["certifications"]) == 2
    assert "Google Professional Cloud Architect" in data["certifications"]


@pytest.mark.asyncio
async def test_portfolio_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_portfolio_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped from _provenance."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "owner_name" in result.provenance
    assert "Jane Smith" in result.provenance["owner_name"].evidence_snippet
    assert result.provenance["owner_name"].artifact_id == artifact.id

    assert "projects" in result.provenance
    assert "Featured Projects" in result.provenance["projects"].evidence_snippet

    assert "skills" in result.provenance
    assert "Python" in result.provenance["skills"].evidence_snippet


@pytest.mark.asyncio
async def test_portfolio_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert result.error_message is not None
    assert "LLM provider mock error during portfolio extraction" in result.error_message
    assert len(result.warnings) > 0
    assert "Extraction failed" in result.warnings[0]


@pytest.mark.asyncio
async def test_portfolio_extractor_disabled_provider_returns_skipped() -> None:
    """Verifies missing API key (disabled provider) returns ExtractionStatus.SKIPPED, never SUCCESS."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(is_disabled=True)

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SKIPPED
    assert result.error_message == "GEMINI_API_KEY is not configured."
    assert any("GEMINI_API_KEY is not configured" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_portfolio_extractor_registry_resolution() -> None:
    """Verifies PortfolioExtractor registration and lookup via ExtractorRegistry."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.PORTFOLIO, extractor_instance)
    resolved = registry.get_extractor(DocumentType.portfolio())

    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_portfolio_extractor_factory_resolution() -> None:
    """Verifies PortfolioExtractor resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.PORTFOLIO, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.portfolio())
    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_portfolio_extractor_flat_structure_fallback() -> None:
    """Verifies post_process handles flat-structure LLM responses (no nested owner_info)."""
    flat_json: dict[str, Any] = {
        "name": "Bob Developer",
        "title": "Backend Engineer",
        "email": "bob@example.com",
        "github_url": "https://github.com/bobdev",
        "projects": [],
        "skills": [{"name": "Go", "category": "Programming Language"}],
        "work_experience": [],
        "education": [],
        "certifications": [],
        "_provenance": {
            "owner_name": "Page title: Bob Developer — Backend Engineer",
        },
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=flat_json)

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    owner = result.structured_data["owner_info"]
    assert owner["name"] == "Bob Developer"
    assert owner["title"] == "Backend Engineer"
    assert owner["email"] == "bob@example.com"
    assert owner["github_url"] == "https://github.com/bobdev"
    assert result.structured_data["skills"] == [{"name": "Go", "category": "Programming Language"}]


@pytest.mark.asyncio
async def test_portfolio_extractor_missing_owner_name_produces_warning() -> None:
    """Verifies that a missing owner name produces a warning but still returns SUCCESS."""
    json_without_name: dict[str, Any] = {
        "owner_info": {
            "name": "",
            "title": "Developer",
        },
        "projects": [],
        "skills": [],
        "work_experience": [],
        "education": [],
        "certifications": [],
        "_provenance": {},
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=json_without_name)

    extractor = PortfolioExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    assert any("owner name" in w for w in result.warnings)

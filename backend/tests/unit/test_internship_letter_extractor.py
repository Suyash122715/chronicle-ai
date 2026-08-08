"""Unit tests for InternshipLetterExtractor with mocked LLM provider."""

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
from app.infrastructure.ai.internship_letter_extractor import InternshipLetterExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider returning canned internship letter extraction responses."""

    def __init__(
        self,
        canned_json: dict[str, Any] | None = None,
        raise_error: bool = False,
        is_disabled: bool = False,
    ) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "internship_info": {
                "intern_name": "Alice Johnson",
                "organization": "TechCorp Solutions Pvt. Ltd.",
                "role": "Software Engineering Intern",
                "department": "Backend Engineering",
                "start_date": "2024-06-01",
                "end_date": "2024-11-30",
                "duration": "6 months",
                "supervisor_name": "Bob Smith",
                "supervisor_designation": "Senior Engineering Manager",
                "stipend": "INR 25,000 per month",
                "location": "Bengaluru, India",
                "letter_type": "completion_letter",
                "issue_date": "2024-12-01",
            },
            "skills": [
                {"name": "Python", "category": "Programming Language"},
                {"name": "FastAPI", "category": "Framework"},
                {"name": "PostgreSQL", "category": "Database"},
            ],
            "responsibilities": [
                "Designed and implemented RESTful APIs using FastAPI.",
                "Optimized database queries reducing p95 latency by 30%.",
                "Participated in code reviews and sprint planning.",
            ],
            "_provenance": {
                "intern_name": "Letter addressed to Alice Johnson",
                "organization": "TechCorp Solutions Pvt. Ltd. letterhead",
                "role": "Role stated as 'Software Engineering Intern' in paragraph 1",
            },
        }
        self.raise_error = raise_error
        self.is_disabled = is_disabled
        self.captured_prompt: str | None = None

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
            raise RuntimeError("LLM provider mock error during internship letter extraction")

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

        self.captured_prompt = prompt
        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 200, "completion_tokens": 120, "total_tokens": 320},
            latency=0.42,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "TechCorp Solutions Pvt. Ltd. - Internship Completion Letter - Alice Johnson") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="internship_letter.pdf",
        stored_filename="stored_internship_letter.pdf",
        file_path="storage/internship_letter.pdf",
        mime_type="application/pdf",
        file_size=2048,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.internship_letter(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_internship_letter_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for internship letter artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data
    info = data["internship_info"]
    assert info["intern_name"] == "Alice Johnson"
    assert info["organization"] == "TechCorp Solutions Pvt. Ltd."
    assert info["role"] == "Software Engineering Intern"
    assert info["department"] == "Backend Engineering"
    assert info["start_date"] == "2024-06-01"
    assert info["end_date"] == "2024-11-30"
    assert info["duration"] == "6 months"
    assert info["letter_type"] == "completion_letter"
    assert info["issue_date"] == "2024-12-01"
    assert len(data["skills"]) == 3
    assert data["skills"][0]["name"] == "Python"
    assert len(data["responsibilities"]) == 3


@pytest.mark.asyncio
async def test_internship_letter_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_internship_letter_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped from _provenance."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "intern_name" in result.provenance
    assert result.provenance["intern_name"].evidence_snippet == "Letter addressed to Alice Johnson"
    assert result.provenance["intern_name"].artifact_id == artifact.id

    assert "organization" in result.provenance
    assert result.provenance["organization"].evidence_snippet == "TechCorp Solutions Pvt. Ltd. letterhead"

    assert "role" in result.provenance
    assert "Software Engineering Intern" in result.provenance["role"].evidence_snippet


@pytest.mark.asyncio
async def test_internship_letter_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert result.error_message is not None
    assert "LLM provider mock error during internship letter extraction" in result.error_message
    assert len(result.warnings) > 0
    assert "Extraction failed" in result.warnings[0]


@pytest.mark.asyncio
async def test_internship_letter_extractor_disabled_provider_returns_skipped() -> None:
    """Verifies that missing API key (disabled provider) returns ExtractionStatus.SKIPPED, never SUCCESS."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(is_disabled=True)

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SKIPPED
    assert result.error_message == "GEMINI_API_KEY is not configured."
    assert any("GEMINI_API_KEY is not configured" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_internship_letter_extractor_registry_resolution() -> None:
    """Verifies InternshipLetterExtractor registration and lookup via ExtractorRegistry."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.INTERNSHIP_LETTER, extractor_instance)
    resolved = registry.get_extractor(DocumentType.internship_letter())

    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_internship_letter_extractor_factory_resolution() -> None:
    """Verifies InternshipLetterExtractor resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.INTERNSHIP_LETTER, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.internship_letter())
    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_internship_letter_extractor_flat_structure_fallback() -> None:
    """Verifies post_process handles flat-structure LLM responses (no nested internship_info)."""
    flat_json: dict[str, Any] = {
        "intern_name": "Charlie Brown",
        "company": "StartupXYZ",
        "role": "Data Science Intern",
        "start_date": "2024-01-10",
        "end_date": "2024-04-10",
        "duration": "3 months",
        "letter_type": "offer_letter",
        "issue_date": "2024-01-05",
        "skills": [],
        "responsibilities": ["Data analysis", "Model training"],
        "_provenance": {
            "intern_name": "Dear Charlie Brown header line",
        },
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=flat_json)

    extractor = InternshipLetterExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    info = result.structured_data["internship_info"]
    assert info["intern_name"] == "Charlie Brown"
    assert info["organization"] == "StartupXYZ"
    assert info["role"] == "Data Science Intern"
    assert info["letter_type"] == "offer_letter"
    assert result.structured_data["responsibilities"] == ["Data analysis", "Model training"]

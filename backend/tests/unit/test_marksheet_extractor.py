"""Unit tests for MarksheetExtractor with mocked LLM provider."""

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
from app.infrastructure.ai.marksheet_extractor import MarksheetExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider capturing invoked arguments and returning canned marksheet responses."""

    def __init__(
        self,
        canned_json: dict[str, Any] | None = None,
        raise_error: bool = False,
        is_disabled: bool = False,
    ) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "academic_info": {
                "institution": "Stanford University",
                "student_name": "Jane Doe",
                "roll_number": "STU-98765",
                "program": "B.S. Computer Science",
                "term": "Spring 2025",
                "cgpa": "3.92",
                "percentage": "95.5",
                "result_status": "Passed",
                "issue_date": "2025-06-01",
            },
            "subjects": [
                {
                    "subject_name": "Algorithms and Data Structures",
                    "subject_code": "CS106B",
                    "marks_obtained": "95",
                    "max_marks": "100",
                    "grade": "A+",
                    "credits": "4",
                },
                {
                    "subject_name": "Operating Systems",
                    "subject_code": "CS140",
                    "marks_obtained": "90",
                    "max_marks": "100",
                    "grade": "A",
                    "credits": "4",
                },
            ],
            "_provenance": {
                "institution": "Stanford University title banner",
                "cgpa": "Cumulative GPA summary at bottom of page",
            },
        }
        self.raise_error = raise_error
        self.is_disabled = is_disabled
        self.captured_prompt: str | None = None
        self.captured_schema: dict[str, Any] | None = None

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
            raise RuntimeError("LLM provider mock error during marksheet extraction")

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
        self.captured_schema = response_schema

        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 150, "completion_tokens": 80, "total_tokens": 230},
            latency=0.35,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "Stanford University Official Transcript - Jane Doe") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="transcript.pdf",
        stored_filename="stored_transcript.pdf",
        file_path="storage/transcript.pdf",
        mime_type="application/pdf",
        file_size=3072,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.marksheet(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_marksheet_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for marksheet artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data
    assert data["academic_info"]["institution"] == "Stanford University"
    assert data["academic_info"]["student_name"] == "Jane Doe"
    assert data["academic_info"]["cgpa"] == "3.92"
    assert len(data["subjects"]) == 2
    assert data["subjects"][0]["subject_name"] == "Algorithms and Data Structures"


@pytest.mark.asyncio
async def test_marksheet_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_marksheet_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "institution" in result.provenance
    assert result.provenance["institution"].evidence_snippet == "Stanford University title banner"
    assert result.provenance["institution"].artifact_id == artifact.id


@pytest.mark.asyncio
async def test_marksheet_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert "Extraction failed" in result.warnings[0]
    assert "LLM provider mock error during marksheet extraction" in result.error_message


@pytest.mark.asyncio
async def test_marksheet_extractor_disabled_provider_returns_skipped() -> None:
    """Verifies that missing API key (disabled provider) returns ExtractionStatus.SKIPPED and never SUCCESS."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(is_disabled=True)

    extractor = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SKIPPED
    assert result.error_message == "GEMINI_API_KEY is not configured."
    assert "GEMINI_API_KEY is not configured" in result.warnings[0]


@pytest.mark.asyncio
async def test_marksheet_extractor_registry_and_factory_resolution() -> None:
    """Verifies MarksheetExtractor registration in ExtractorRegistry and resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = MarksheetExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.MARKSHEET, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.marksheet())
    assert resolved is not None
    assert resolved == extractor_instance

"""Unit tests for ResumeExtractor with mocked LLM provider."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.llm_response import LLMResponse
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository
from app.infrastructure.ai.resume_extractor import ResumeExtractor


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider capturing invoked arguments and returning canned responses."""

    def __init__(self, canned_json: dict[str, Any] | None = None, raise_error: bool = False) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "personal_info": {"full_name": "Jane Doe", "email": "jane@example.com"},
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "education": [{"institution": "MIT", "degree": "B.S. CS"}],
            "work_experience": [{"company": "Tech Corp", "role": "Senior Engineer"}],
            "projects": [{"name": "Chronicle AI", "tech": ["Python"]}],
            "certifications": ["AWS Certified Solutions Architect"],
            "_provenance": {
                "skills": "Listed under Technical Skills section",
                "personal_info": "Header at top of page",
            },
        }
        self.raise_error = raise_error
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
            raise RuntimeError("LLM provider mock error")

        self.captured_prompt = prompt
        self.captured_schema = response_schema

        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency=0.25,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "Jane Doe\nEmail: jane@example.com\nSkills: Python, FastAPI") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="jane_resume.pdf",
        stored_filename="stored_jane_resume.pdf",
        file_path="storage/jane_resume.pdf",
        mime_type="application/pdf",
        file_size=4096,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.resume(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resume_extractor_prepare_variables() -> None:
    """Verifies prepare_variables returns document_text, document_type, and output_schema."""
    artifact = make_artifact("Sample Resume Text")
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=mock_provider)

    variables = extractor.prepare_variables(artifact, classification)

    assert "document_text" in variables
    assert variables["document_text"] == "Sample Resume Text"
    assert "document_type" in variables
    assert variables["document_type"] == "Resume"
    assert "output_schema" in variables
    assert isinstance(variables["output_schema"], dict)


@pytest.mark.asyncio
async def test_resume_extractor_prompt_loading_and_variables() -> None:
    """Verifies prompt loading from FileSystemPromptRepository and variable substitution."""
    artifact = make_artifact("John Smith - Full Stack Developer")
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    assert mock_provider.captured_prompt is not None
    assert "John Smith - Full Stack Developer" in mock_provider.captured_prompt
    assert mock_provider.captured_schema is not None


@pytest.mark.asyncio
async def test_resume_extractor_field_mapping() -> None:
    """Verifies parsed JSON fields (skills, education, experience, projects, certifications) are mapped correctly."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    data = result.structured_data
    assert data["personal_info"] == {"full_name": "Jane Doe", "email": "jane@example.com"}
    assert data["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["education"] == [{"institution": "MIT", "degree": "B.S. CS"}]
    assert data["experience"] == [{"company": "Tech Corp", "role": "Senior Engineer"}]
    assert data["projects"] == [{"name": "Chronicle AI", "tech": ["Python"]}]
    assert data["certifications"] == ["AWS Certified Solutions Architect"]


@pytest.mark.asyncio
async def test_resume_extractor_provenance() -> None:
    """Verifies field provenance is populated correctly from _provenance object."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "skills" in result.provenance
    assert isinstance(result.provenance["skills"], Provenance)
    assert result.provenance["skills"].evidence_snippet == "Listed under Technical Skills section"
    assert result.provenance["skills"].artifact_id == artifact.id


@pytest.mark.asyncio
async def test_resume_extractor_graceful_missing_fields_and_warnings() -> None:
    """Verifies missing fields default to empty lists/dicts and generate warnings."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()

    # Provider returns incomplete JSON without skills or provenance
    incomplete_json = {
        "personal_info": {"full_name": "Bob Builder"},
        "education": [],
    }
    mock_provider = MockLLMProvider(canned_json=incomplete_json)

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data
    assert data["skills"] == []
    assert data["experience"] == []
    assert data["projects"] == []
    assert data["certifications"] == []
    assert len(result.warnings) == 1
    assert "Missing or invalid 'skills' field" in result.warnings[0]


@pytest.mark.asyncio
async def test_resume_extractor_null_llm_response() -> None:
    """Verifies null LLM parsed_json produces FAILED/warning result gracefully."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()

    class NullLLMProvider(LLMProviderInterface):
        async def generate_structured(self, prompt: str, response_schema: dict, **kwargs) -> LLMResponse:
            return LLMResponse(
                raw_response="",
                parsed_json=None,
                token_usage={},
                latency=0.1,
                provider="null",
                model="null",
                finish_reason="STOP",
                prompt_version="v1",
            )

    extractor = ResumeExtractor(prompt_repository=repo, llm_provider=NullLLMProvider())
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    assert result.structured_data["skills"] == []
    assert len(result.warnings) == 1
    assert "LLM returned no parsed JSON content" in result.warnings[0]

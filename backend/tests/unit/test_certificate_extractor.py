"""Unit tests for CertificateExtractor with mocked LLM provider."""

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
from app.infrastructure.ai.certificate_extractor import CertificateExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider capturing invoked arguments and returning canned certificate responses."""

    def __init__(self, canned_json: dict[str, Any] | None = None, raise_error: bool = False) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "certificate_info": {
                "title": "AWS Certified Solutions Architect",
                "issuer": "Amazon Web Services",
                "recipient_name": "Jane Doe",
                "issue_date": "2025-06-15",
                "expiry_date": "2028-06-15",
                "credential_id": "AWS-123456",
                "verification_url": "https://aws.amazon.com/verify/123456",
            },
            "skills": ["Cloud Architecture", "AWS", "DynamoDB", "S3"],
            "_provenance": {
                "title": "Header title of the certificate",
                "issuer": "Issued by Amazon Web Services logo",
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
            raise RuntimeError("LLM provider mock error during certificate extraction")

        self.captured_prompt = prompt
        self.captured_schema = response_schema

        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
            latency=0.3,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "AWS Certified Solutions Architect - Jane Doe") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="aws_cert.pdf",
        stored_filename="stored_aws_cert.pdf",
        file_path="storage/aws_cert.pdf",
        mime_type="application/pdf",
        file_size=2048,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.certificate(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_certificate_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for certificate artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = CertificateExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data
    assert data["certificate_info"]["title"] == "AWS Certified Solutions Architect"
    assert data["certificate_info"]["issuer"] == "Amazon Web Services"
    assert data["certificate_info"]["recipient_name"] == "Jane Doe"
    assert data["skills"] == ["Cloud Architecture", "AWS", "DynamoDB", "S3"]


@pytest.mark.asyncio
async def test_certificate_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = CertificateExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_certificate_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = CertificateExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "title" in result.provenance
    assert result.provenance["title"].evidence_snippet == "Header title of the certificate"
    assert result.provenance["title"].artifact_id == artifact.id


@pytest.mark.asyncio
async def test_certificate_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = CertificateExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert "Extraction failed" in result.warnings[0]
    assert "LLM provider mock error during certificate extraction" in result.error_message


@pytest.mark.asyncio
async def test_certificate_extractor_registry_and_factory_resolution() -> None:
    """Verifies CertificateExtractor registration in ExtractorRegistry and resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo = FileSystemPromptRepository()
    extractor_instance = CertificateExtractor(prompt_repository=repo, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.CERTIFICATE, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.certificate())
    assert resolved is not None
    assert resolved == extractor_instance

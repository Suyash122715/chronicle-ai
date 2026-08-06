"""Unit tests for ExtractorExecutionService and ExtractorFactory."""

import uuid
from datetime import datetime, timezone
import pytest

from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.dependencies import get_extractor_execution_service, get_extractor_factory
from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.services.extractor_factory import ExtractorFactory
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance


class FakeSuccessfulExtractor(ArtifactExtractorInterface):
    """Fake extractor implementation that returns a successful extraction result."""

    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        return ExtractionResult(
            artifact_id=artifact.id,
            document_type=classification_result.document_type,
            structured_data={"key": "extracted_value"},
            provenance={"key": Provenance(artifact_id=artifact.id, confidence="HIGH")},
            confidence=ConfidenceLevel.HIGH,
            status=ExtractionStatus.SUCCESS,
        )


class FakeFailingExtractor(ArtifactExtractorInterface):
    """Fake extractor implementation that raises an exception during extraction."""

    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        raise RuntimeError("LLM provider connection failed")


@pytest.fixture
def sample_artifact() -> Artifact:
    """Fixture providing a standard test Artifact entity."""
    return Artifact(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        filename="test_document.pdf",
        stored_filename="stored_test.pdf",
        file_path="/storage/test_document.pdf",
        file_size=2048,
        mime_type="application/pdf",
    )


class TestExtractorFactory:
    """Test suite for ExtractorFactory resolution and instantiation."""

    def test_factory_resolves_and_instantiates_registered_class(self) -> None:
        """Verifies factory resolves registered extractor class into an instance."""
        registry = ExtractorRegistry()
        registry.register(DocumentType.resume(), FakeSuccessfulExtractor)

        factory = ExtractorFactory(registry)
        extractor = factory.get_extractor(DocumentType.resume())

        assert extractor is not None
        assert isinstance(extractor, FakeSuccessfulExtractor)

    def test_factory_returns_none_for_unregistered_document_type(self) -> None:
        """Verifies factory returns None when document type has no registered extractor."""
        registry = ExtractorRegistry()
        factory = ExtractorFactory(registry)

        extractor = factory.get_extractor("NonExistentDocType")
        assert extractor is None


class TestExtractorExecutionService:
    """Test suite for ExtractorExecutionService orchestration logic."""

    @pytest.mark.asyncio
    async def test_successful_extraction_execution(self, sample_artifact: Artifact) -> None:
        """Verifies successful extractor execution returns ExtractionResult with SUCCESS status."""
        registry = ExtractorRegistry()
        registry.register(DocumentType.resume(), FakeSuccessfulExtractor)
        factory = ExtractorFactory(registry)
        service = ExtractorExecutionService(factory)

        result = await service.execute(sample_artifact, DocumentType.resume())

        assert result.status == ExtractionStatus.SUCCESS
        assert result.artifact_id == sample_artifact.id
        assert result.document_type == DocumentType.resume()
        assert result.structured_data == {"key": "extracted_value"}
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_unsupported_document_type_returns_not_supported_status(
        self,
        sample_artifact: Artifact,
    ) -> None:
        """Verifies unsupported document type returns NOT_SUPPORTED status without throwing."""
        registry = ExtractorRegistry()  # Empty registry
        factory = ExtractorFactory(registry)
        service = ExtractorExecutionService(factory)

        result = await service.execute(sample_artifact, DocumentType.certificate())

        assert result.status == ExtractionStatus.NOT_SUPPORTED
        assert result.artifact_id == sample_artifact.id
        assert result.document_type == DocumentType.certificate()
        assert result.structured_data == {}
        assert "No extractor registered" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_extractor_failure_returns_failed_status_without_throwing(
        self,
        sample_artifact: Artifact,
    ) -> None:
        """Verifies failing extractor returns FAILED status and error details without throwing."""
        registry = ExtractorRegistry()
        registry.register(DocumentType.marksheet(), FakeFailingExtractor)
        factory = ExtractorFactory(registry)
        service = ExtractorExecutionService(factory)

        result = await service.execute(sample_artifact, DocumentType.marksheet())

        assert result.status == ExtractionStatus.FAILED
        assert result.artifact_id == sample_artifact.id
        assert result.document_type == DocumentType.marksheet()
        assert result.error_message == "LLM provider connection failed"
        assert len(result.warnings) > 0
        assert "LLM provider connection failed" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_execution_accepts_string_enum_and_value_object(
        self,
        sample_artifact: Artifact,
    ) -> None:
        """Verifies execute accepts DocumentType value object, DocumentTypeEnum, and string inputs."""
        registry = ExtractorRegistry()
        registry.register(DocumentTypeEnum.RESUME, FakeSuccessfulExtractor)
        factory = ExtractorFactory(registry)
        service = ExtractorExecutionService(factory)

        # 1. DocumentType value object
        res1 = await service.execute(sample_artifact, DocumentType.resume())
        assert res1.status == ExtractionStatus.SUCCESS

        # 2. DocumentTypeEnum
        res2 = await service.execute(sample_artifact, DocumentTypeEnum.RESUME)
        assert res2.status == ExtractionStatus.SUCCESS

        # 3. String representation
        res3 = await service.execute(sample_artifact, "Resume")
        assert res3.status == ExtractionStatus.SUCCESS

    def test_fastapi_dependency_injection_provider(self) -> None:
        """Verifies dependency providers return correctly wired ExtractorExecutionService."""
        registry = ExtractorRegistry()
        registry.register(DocumentTypeEnum.RESUME, FakeSuccessfulExtractor)

        factory = get_extractor_factory(registry)
        assert isinstance(factory, ExtractorFactory)

        service = get_extractor_execution_service(factory)
        assert isinstance(service, ExtractorExecutionService)

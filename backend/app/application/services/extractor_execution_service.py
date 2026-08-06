"""ExtractorExecutionService application service."""

from datetime import datetime, timezone

from app.domain.entities.artifact import Artifact
from app.domain.services.extractor_factory import ExtractorFactory
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.extractor_execution_service")


class ExtractorExecutionService:
    """Application orchestration service for artifact entity extraction.

    Coordinates extraction by requesting an extractor instance from ExtractorFactory and
    executing the extractor interface. Enforces zero document-type conditional logic.
    """

    def __init__(self, extractor_factory: ExtractorFactory) -> None:
        self._extractor_factory = extractor_factory

    async def execute(
        self,
        artifact: Artifact,
        document_type: DocumentType | DocumentTypeEnum | str,
        classification_result: ClassificationResult | None = None,
    ) -> ExtractionResult:
        """Executes extraction for an artifact and document type.

        Args:
            artifact: Target domain Artifact entity.
            document_type: DocumentType value object, enum, or string.
            classification_result: Optional classification result. Created if not provided.

        Returns:
            Canonical ExtractionResult value object. Never throws exceptions.
        """
        started_at = datetime.now(timezone.utc)

        # 1. Normalize document type to DocumentType value object
        doc_type_vo = self._normalize_document_type(document_type)

        # 2. Normalize classification result
        if classification_result is None:
            classification_result = ClassificationResult(
                document_type=doc_type_vo,
                confidence_level=ConfidenceLevel.HIGH,
                classifier_version="1.0.0",
                classified_at=artifact.created_at if hasattr(artifact, "created_at") and artifact.created_at else started_at,
                provenance=Provenance(artifact_id=artifact.id, confidence="HIGH"),
            )

        # 3. Request extractor from ExtractorFactory
        extractor = self._extractor_factory.get_extractor(doc_type_vo)

        # 4. Handle unsupported document type (no extractor registered)
        if extractor is None:
            logger.info("No extractor registered for document type '%s'", doc_type_vo.value)
            return ExtractionResult(
                artifact_id=artifact.id,
                document_type=doc_type_vo,
                structured_data={},
                provenance={},
                warnings=[f"No extractor registered for document type: {doc_type_vo.value}"],
                confidence=ConfidenceLevel.LOW,
                extractor_version="1.0.0",
                prompt_version="v1",
                llm_metadata={},
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                status=ExtractionStatus.NOT_SUPPORTED,
                error_message=f"No extractor registered for document type: {doc_type_vo.value}",
            )

        # 5. Execute extractor with error handling
        try:
            return await extractor.extract(artifact, classification_result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Extractor execution failed for artifact %s: %s", artifact.id, str(exc))
            return ExtractionResult(
                artifact_id=artifact.id,
                document_type=doc_type_vo,
                structured_data={},
                provenance={},
                warnings=[f"Extraction failed: {exc}"],
                confidence=ConfidenceLevel.LOW,
                extractor_version="1.0.0",
                prompt_version="v1",
                llm_metadata={},
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                status=ExtractionStatus.FAILED,
                error_message=str(exc),
            )

    def _normalize_document_type(
        self,
        document_type: DocumentType | DocumentTypeEnum | str,
    ) -> DocumentType:
        """Normalizes document type input into a DocumentType value object."""
        if isinstance(document_type, DocumentType):
            return document_type
        if isinstance(document_type, DocumentTypeEnum):
            return DocumentType(document_type)
        if isinstance(document_type, str):
            return DocumentType.from_str(document_type)
        return DocumentType.unknown()

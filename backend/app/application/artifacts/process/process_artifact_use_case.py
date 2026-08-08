"""Process Artifact Use Case implementation."""

from datetime import datetime, timezone
from uuid import UUID

from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.domain.entities.artifact import ProcessingStatus
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.process_artifact")


class ProcessArtifactUseCase:
    """Application use case for asynchronously processing an uploaded artifact.

    Orchestrates the background processing pipeline:
    1. Updates status to PROCESSING.
    2. Performs deterministic classification.
    3. Persists classification metadata.
    4. Executes document extraction via ExtractorExecutionService.
    5. Updates status to COMPLETED.
    """

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        storage_service: StorageServiceInterface,
        document_classifier: DocumentClassifierInterface,
        extractor_execution_service: ExtractorExecutionService | None = None,
        max_retries: int = 3,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service
        self._document_classifier = document_classifier
        self._extractor_execution_service = extractor_execution_service
        self._max_retries = max_retries

    async def execute(self, artifact_id: UUID) -> None:
        """Executes asynchronous artifact processing for the given artifact ID."""
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None:
            logger.warning("Background processing requested for non-existent artifact ID: %s", artifact_id)
            return

        # 1. Update status to PROCESSING
        artifact.status = ProcessingStatus.PROCESSING
        artifact.updated_at = datetime.now(timezone.utc)
        await self._artifact_repository.update(artifact)

        try:
            # 2. Perform deterministic classification (no file content needed)
            classification_result = await self._document_classifier.classify(
                artifact_id=artifact.id,
                filename=artifact.filename,
                mime_type=artifact.mime_type,
                file_size=artifact.file_size,
                metadata={},
            )

            # 3. Persist classification metadata
            artifact.document_type = classification_result.document_type
            artifact.classification_confidence = classification_result.confidence_level
            artifact.classifier_version = classification_result.classifier_version
            artifact.classified_at = classification_result.classified_at

            # 4. Perform extraction via ExtractorExecutionService if available
            if self._extractor_execution_service is not None:
                try:
                    extraction_result = await self._extractor_execution_service.execute(
                        artifact=artifact,
                        document_type=classification_result.document_type,
                        classification_result=classification_result,
                    )
                    logger.info(
                        "Extraction completed for artifact %s: status=%s, warnings=%s",
                        artifact_id,
                        extraction_result.status.value if hasattr(extraction_result.status, "value") else extraction_result.status,
                        extraction_result.warnings,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error("Extraction execution failed for artifact %s (non-fatal): %s", artifact_id, str(exc))

            # 5. Mark COMPLETED
            artifact.status = ProcessingStatus.COMPLETED
            artifact.updated_at = datetime.now(timezone.utc)
            await self._artifact_repository.update(artifact)
            logger.info(
                "Successfully processed artifact %s (classified as %s)",
                artifact_id,
                artifact.document_type,
            )

        except Exception as exc:
            # 6. Exception handling & retry tracking
            artifact.retry_count += 1
            artifact.updated_at = datetime.now(timezone.utc)

            if artifact.retry_count >= self._max_retries:
                artifact.status = ProcessingStatus.FAILED
                artifact.error_message = f"Processing failed after {artifact.retry_count} attempt(s): {str(exc)}"
                logger.error("Artifact %s failed permanently after %d retries: %s", artifact_id, artifact.retry_count, str(exc))
            else:
                artifact.status = ProcessingStatus.FAILED
                artifact.error_message = f"Attempt {artifact.retry_count} failed: {str(exc)}"
                logger.warning("Artifact %s attempt %d failed: %s", artifact_id, artifact.retry_count, str(exc))

            await self._artifact_repository.update(artifact)

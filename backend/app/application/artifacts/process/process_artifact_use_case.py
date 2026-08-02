"""Process Artifact Use Case implementation."""

from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.artifact import ProcessingStatus
from app.domain.exceptions.artifact_exceptions import StorageError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface

from app.domain.interfaces.storage_service import StorageServiceInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.infrastructure.processing.deterministic_classifier import DeterministicDocumentClassifier
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.process_artifact")


class ProcessArtifactUseCase:
    """Application use case for asynchronously processing an uploaded artifact.

    Orchestrates the background processing pipeline:
    1. Updates status to PROCESSING.
    2. Fetches raw file bytes from physical storage.
    3. Extracts raw string text via TextExtractorInterface.
    4. On success: Updates status to COMPLETED and stores raw_text.
    5. On failure: Manages retry counter and transitions status to FAILED after max retries.
    """

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        storage_service: StorageServiceInterface,
        document_classifier: DocumentClassifierInterface,
        max_retries: int = 3,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service
        self._document_classifier = document_classifier
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

            # 3. Persist classification metadata and mark COMPLETED
            artifact.document_type = classification_result.document_type
            artifact.classification_confidence = classification_result.confidence_level
            artifact.classifier_version = classification_result.classifier_version
            artifact.classified_at = classification_result.classified_at
            artifact.status = ProcessingStatus.COMPLETED
            artifact.updated_at = datetime.now(timezone.utc)
            await self._artifact_repository.update(artifact)
            logger.info(
                "Successfully classified artifact %s as %s with confidence %s",
                artifact_id,
                artifact.document_type,
                artifact.classification_confidence,
            )

        except Exception as exc:
            # 5. Exception handling & retry tracking
            artifact.retry_count += 1
            artifact.updated_at = datetime.now(timezone.utc)

            if artifact.retry_count >= self._max_retries:
                artifact.status = ProcessingStatus.FAILED
                artifact.error_message = f"Processing failed after {artifact.retry_count} attempt(s): {str(exc)}"
                logger.error("Artifact %s failed permanently after %d retries: %s", artifact_id, artifact.retry_count, str(exc))
            else:
                artifact.status = ProcessingStatus.FAILED  # Marked failed for current attempt, retry counter preserved
                artifact.error_message = f"Attempt {artifact.retry_count} failed: {str(exc)}"
                logger.warning("Artifact %s attempt %d failed: %s", artifact_id, artifact.retry_count, str(exc))

            await self._artifact_repository.update(artifact)

"""Process Artifact Use Case implementation."""

from datetime import datetime, timezone
from uuid import UUID

from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.domain.entities.artifact import ProcessingStatus
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
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
    5. Persists extraction result (all statuses) via ExtractionRepositoryInterface.
    6. Builds and persists Knowledge Graph candidates via KnowledgeGraphRepositoryInterface (non-fatal).
    7. Updates status to COMPLETED.
    """

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        storage_service: StorageServiceInterface,
        document_classifier: DocumentClassifierInterface,
        extractor_execution_service: ExtractorExecutionService | None = None,
        extraction_repository: ExtractionRepositoryInterface | None = None,
        knowledge_graph_repository: KnowledgeGraphRepositoryInterface | None = None,
        build_knowledge_graph_use_case: BuildKnowledgeGraphUseCase | None = None,
        max_retries: int = 3,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service
        self._document_classifier = document_classifier
        self._extractor_execution_service = extractor_execution_service
        self._extraction_repository = extraction_repository
        self._knowledge_graph_repository = knowledge_graph_repository
        self._build_knowledge_graph_use_case = build_knowledge_graph_use_case
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

                    # 5. Persist extraction result for ALL statuses
                    saved_extraction = None
                    if self._extraction_repository is not None:
                        try:
                            saved_extraction = await self._extraction_repository.save(extraction_result)
                            logger.info(
                                "Extraction result persisted for artifact %s (status=%s)",
                                artifact_id,
                                extraction_result.status.value if hasattr(extraction_result.status, "value") else extraction_result.status,
                            )
                        except Exception as persist_exc:  # noqa: BLE001
                            logger.error(
                                "Extraction persistence failed for artifact %s (non-fatal): %s",
                                artifact_id,
                                str(persist_exc),
                            )

                    # 6. Build and persist Knowledge Graph candidates (non-fatal, after extraction persistence)
                    if self._knowledge_graph_repository is not None and (
                        saved_extraction is not None or self._extraction_repository is None
                    ):
                        try:
                            graph_builder = self._build_knowledge_graph_use_case or BuildKnowledgeGraphUseCase()
                            extraction_id = getattr(saved_extraction, "id", None) if saved_extraction else None
                            candidates = graph_builder.execute(
                                user_id=artifact.user_id,
                                artifact_id=artifact.id,
                                extraction_result=extraction_result,
                                extraction_id=extraction_id,
                            )
                            if candidates.entities or candidates.relationships:
                                await self._knowledge_graph_repository.persist_graph(
                                    entities=candidates.entities,
                                    relationships=candidates.relationships,
                                    entity_provenance=candidates.entity_provenance,
                                    relationship_provenance=candidates.relationship_provenance,
                                )
                                logger.info(
                                    "Knowledge graph successfully persisted for artifact %s: %d entities, %d relationships",
                                    artifact_id,
                                    len(candidates.entities),
                                    len(candidates.relationships),
                                )
                        except Exception as kg_exc:  # noqa: BLE001
                            logger.error(
                                "Knowledge graph generation/persistence failed for artifact %s (non-fatal): %s",
                                artifact_id,
                                str(kg_exc),
                                exc_info=True,
                            )
                except Exception as exc:  # noqa: BLE001
                    logger.error("Extraction execution failed for artifact %s (non-fatal): %s", artifact_id, str(exc))

            # 7. Mark COMPLETED
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

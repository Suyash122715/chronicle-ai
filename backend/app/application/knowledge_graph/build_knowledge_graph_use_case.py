"""BuildKnowledgeGraphUseCase — Application use case orchestrating graph candidate generation from extraction results."""

from uuid import UUID

from app.application.knowledge_graph.extraction_graph_mapper import ExtractionGraphMapper, GraphCandidates
from app.domain.exceptions.base import DomainValidationError
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.build_knowledge_graph")


class BuildKnowledgeGraphUseCase:
    """Application use case that orchestrates the conversion of an ExtractionResult into Knowledge Graph candidates.

    Validates ownership context, enforces extraction status rules, and delegates candidate mapping to ExtractionGraphMapper.
    """

    def __init__(self, mapper: ExtractionGraphMapper | None = None) -> None:
        self._mapper = mapper or ExtractionGraphMapper()

    def execute(
        self,
        user_id: UUID,
        artifact_id: UUID,
        extraction_result: ExtractionResult,
        extraction_id: UUID | None = None,
    ) -> GraphCandidates:
        """Executes knowledge graph building logic for the given extraction result.

        Validates artifact_id alignment and returns GraphCandidates containing generated entities, relationships, and provenance.
        """
        if extraction_result.artifact_id != artifact_id:
            raise DomainValidationError(
                f"Extraction artifact ID mismatch: expected {artifact_id}, got {extraction_result.artifact_id}."
            )

        logger.info(
            "Building Knowledge Graph candidates for artifact %s (status=%s)",
            artifact_id,
            extraction_result.status.value,
        )

        candidates = self._mapper.map_extraction_to_graph(
            user_id=user_id,
            artifact_id=artifact_id,
            extraction_id=extraction_id,
            extraction_result=extraction_result,
        )

        logger.info(
            "Generated %d graph entities and %d relationships for artifact %s",
            len(candidates.entities),
            len(candidates.relationships),
            artifact_id,
        )

        return candidates

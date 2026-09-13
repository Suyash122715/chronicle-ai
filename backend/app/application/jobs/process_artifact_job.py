"""Process Artifact Job — background Unit-of-Work with its own session lifecycle.

Design rationale:
  FastAPI's generator-based dependencies (get_db_session) commit and close the
  session BEFORE the response is sent and BEFORE BackgroundTasks execute.
  Therefore process_use_case.execute() — which is enqueued as a BackgroundTask —
  runs against an already-closed session.

  In production, this job creates a fresh AsyncSession for each background invocation,
  executes ProcessArtifactUseCase inside it, and commits on success / rolls back on failure.
  This is the canonical Unit-of-Work boundary for background processing.

  When running in test environments where repositories are overridden (e.g. InMemoryArtifactRepository),
  it delegates directly to the injected ProcessArtifactUseCase without attempting a database connection.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from app.infrastructure.repositories.extraction_repository import SQLAlchemyExtractionRepository
from app.infrastructure.repositories.knowledge_graph_repository import SQLAlchemyKnowledgeGraphRepository

logger = get_logger("chronicle_ai.jobs.process_artifact")


class ProcessArtifactJob:
    """Runs artifact processing in a dedicated background Unit-of-Work session."""

    def __init__(
        self,
        storage_service: StorageServiceInterface,
        document_classifier: DocumentClassifierInterface,
        extractor_execution_service: ExtractorExecutionService | None = None,
        build_knowledge_graph_use_case: BuildKnowledgeGraphUseCase | None = None,
        process_artifact_use_case: ProcessArtifactUseCase | None = None,
        artifact_repository: ArtifactRepositoryInterface | None = None,
    ) -> None:
        self._storage_service = storage_service
        self._document_classifier = document_classifier
        self._extractor_execution_service = extractor_execution_service
        self._build_knowledge_graph_use_case = build_knowledge_graph_use_case or BuildKnowledgeGraphUseCase()
        self._process_artifact_use_case = process_artifact_use_case
        self._artifact_repository = artifact_repository

    async def execute(self, artifact_id: UUID) -> None:
        """Runs background artifact processing.

        If running in a test context with in-memory repository overrides,
        delegates directly to the injected use case.
        In production with SQLAlchemy repositories, opens a dedicated AsyncSession,
        executes the use case, and commits.
        """
        if self._process_artifact_use_case is not None and not isinstance(
            self._artifact_repository, SQLAlchemyArtifactRepository
        ):
            await self._process_artifact_use_case.execute(artifact_id)
            return

        async with async_session_factory() as session:
            try:
                use_case = ProcessArtifactUseCase(
                    artifact_repository=SQLAlchemyArtifactRepository(session),
                    storage_service=self._storage_service,
                    document_classifier=self._document_classifier,
                    extractor_execution_service=self._extractor_execution_service,
                    extraction_repository=SQLAlchemyExtractionRepository(session),
                    knowledge_graph_repository=SQLAlchemyKnowledgeGraphRepository(session),
                    build_knowledge_graph_use_case=self._build_knowledge_graph_use_case,
                )
                await use_case.execute(artifact_id)
                await session.commit()
                logger.info(
                    "Background processing committed for artifact %s", artifact_id
                )
            except Exception as exc:
                await session.rollback()
                logger.error(
                    "Background processing rolled back for artifact %s: %s",
                    artifact_id,
                    str(exc),
                    exc_info=True,
                )
                raise

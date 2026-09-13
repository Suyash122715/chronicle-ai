"""Unit tests for Knowledge Graph FastAPI dependency injection providers in dependencies.py."""

from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.dependencies import (
    get_build_knowledge_graph_use_case,
    get_knowledge_graph_repository,
    get_process_artifact_use_case,
)
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.infrastructure.repositories.knowledge_graph_repository import SQLAlchemyKnowledgeGraphRepository


def test_get_knowledge_graph_repository_returns_instance() -> None:
    """Verifies get_knowledge_graph_repository returns a SQLAlchemyKnowledgeGraphRepository instance."""
    mock_session = MagicMock(spec=AsyncSession)
    repo = get_knowledge_graph_repository(mock_session)
    assert isinstance(repo, SQLAlchemyKnowledgeGraphRepository)
    assert isinstance(repo, KnowledgeGraphRepositoryInterface)


def test_get_build_knowledge_graph_use_case_returns_instance() -> None:
    """Verifies get_build_knowledge_graph_use_case returns a BuildKnowledgeGraphUseCase instance."""
    use_case = get_build_knowledge_graph_use_case()
    assert isinstance(use_case, BuildKnowledgeGraphUseCase)


def test_get_process_artifact_use_case_wires_all_dependencies() -> None:
    """Verifies get_process_artifact_use_case properly wires all required and KG dependencies."""
    mock_artifact_repo = MagicMock(spec=ArtifactRepositoryInterface)
    mock_storage = MagicMock(spec=StorageServiceInterface)
    mock_classifier = MagicMock(spec=DocumentClassifierInterface)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extraction_repo = MagicMock(spec=ExtractionRepositoryInterface)
    mock_kg_repo = MagicMock(spec=KnowledgeGraphRepositoryInterface)
    mock_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)

    use_case = get_process_artifact_use_case(
        artifact_repository=mock_artifact_repo,
        storage_service=mock_storage,
        document_classifier=mock_classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=mock_extraction_repo,
        knowledge_graph_repository=mock_kg_repo,
        build_knowledge_graph_use_case=mock_builder,
    )

    assert isinstance(use_case, ProcessArtifactUseCase)
    assert use_case._artifact_repository is mock_artifact_repo
    assert use_case._storage_service is mock_storage
    assert use_case._document_classifier is mock_classifier
    assert use_case._extractor_execution_service is mock_extractor_service
    assert use_case._extraction_repository is mock_extraction_repo
    assert use_case._knowledge_graph_repository is mock_kg_repo
    assert use_case._build_knowledge_graph_use_case is mock_builder


def test_get_process_artifact_job_returns_instance() -> None:
    """Verifies get_process_artifact_job returns a ProcessArtifactJob properly wired."""
    from app.application.jobs.process_artifact_job import ProcessArtifactJob
    from app.dependencies import get_process_artifact_job

    mock_storage = MagicMock(spec=StorageServiceInterface)
    mock_classifier = MagicMock(spec=DocumentClassifierInterface)
    mock_extractor = MagicMock(spec=ExtractorExecutionService)
    mock_kg_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)
    mock_use_case = MagicMock(spec=ProcessArtifactUseCase)
    mock_artifact_repo = MagicMock(spec=ArtifactRepositoryInterface)

    job = get_process_artifact_job(
        storage_service=mock_storage,
        document_classifier=mock_classifier,
        extractor_execution_service=mock_extractor,
        build_knowledge_graph_use_case=mock_kg_builder,
        process_artifact_use_case=mock_use_case,
        artifact_repository=mock_artifact_repo,
    )
    assert isinstance(job, ProcessArtifactJob)
    assert job._storage_service is mock_storage
    assert job._document_classifier is mock_classifier
    assert job._extractor_execution_service is mock_extractor
    assert job._process_artifact_use_case is mock_use_case
    assert job._artifact_repository is mock_artifact_repo



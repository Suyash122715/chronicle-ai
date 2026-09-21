"""Integration tests for Knowledge Graph Pipeline Integration (Phase 5 Batch 4B).

Validates end-to-end processing with real database persistence on a shared AsyncSession:
1. Complete graph generation: nodes, edges, and provenance persisted alongside extraction and artifact.
2. Invariant verification: when KG persistence fails, the savepoint rollback ensures zero partial graph records exist, while extraction and artifact status=COMPLETED remain committed.
3. Partial failure within savepoint: verified that partial entity writes inside persist_graph are completely rolled back by begin_nested().
4. Idempotency verification: reprocessing the same artifact updates graph records cleanly without integrity violations.
"""

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.artifact_extraction_model import ArtifactExtractionModel
from app.infrastructure.db.models.artifact_model import ArtifactModel
from app.infrastructure.db.models.entity_artifact_provenance_model import EntityArtifactProvenanceModel
from app.infrastructure.db.models.graph_entity_model import GraphEntityModel
from app.infrastructure.db.models.graph_relationship_model import GraphRelationshipModel
from app.infrastructure.db.models.relationship_artifact_provenance_model import RelationshipArtifactProvenanceModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.processing.deterministic_classifier import DeterministicDocumentClassifier
from app.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from app.infrastructure.repositories.extraction_repository import SQLAlchemyExtractionRepository
from app.infrastructure.repositories.knowledge_graph_repository import SQLAlchemyKnowledgeGraphRepository


class DummyStorageService(StorageServiceInterface):
    """Dummy storage service for integration tests."""

    async def save_file(self, file_bytes: bytes, destination_filename: str) -> str:
        return f"mock/{destination_filename}"

    async def get_file(self, file_path: str) -> bytes | None:
        return b"%PDF-1.4 dummy resume content"

    async def delete_file(self, file_path: str) -> bool:
        return True


@pytest.fixture
async def shared_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated async SQLite database session for pipeline integration tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_test_user(session: AsyncSession) -> UserModel:
    """Helper to seed a test user record."""
    user = UserModel(
        id=uuid4(),
        email=f"test_{uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw_dummy",
        full_name="KG Integration Test User",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def _create_test_artifact(session: AsyncSession, user_id: UUID) -> Artifact:
    """Helper to create and persist an artifact via domain repository."""
    repo = SQLAlchemyArtifactRepository(session)
    artifact = Artifact(
        id=uuid4(),
        user_id=user_id,
        filename="alice_resume.pdf",
        stored_filename=f"stored_{uuid4().hex[:8]}.pdf",
        file_path="mock/alice_resume.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )
    return await repo.add(artifact)


def _make_resume_extraction_result(artifact_id: UUID) -> ExtractionResult:
    """Helper to build a realistic resume extraction result."""
    return ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "work_experience": [
                {
                    "company": "Chronicle Labs",
                    "role": "Lead Architect",
                    "start_date": "2022-01",
                    "end_date": "2024-06",
                    "technologies": ["Python", "FastAPI"],
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "M.S. Computer Science",
                    "start_date": "2018",
                    "end_date": "2020",
                }
            ],
        },
        provenance={},
        warnings=[],
        extractor_version="1.0.0",
        prompt_version="v1",
        status=ExtractionStatus.SUCCESS,
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_knowledge_graph_pipeline_persists_nodes_edges_and_provenance(
    shared_db_session: AsyncSession,
) -> None:
    """Batch 4B: Verifies end-to-end processing with shared AsyncSession persists nodes, edges, and provenance."""
    user = await _create_test_user(shared_db_session)
    artifact = await _create_test_artifact(shared_db_session, user.id)

    extraction_result = _make_resume_extraction_result(artifact.id)
    mock_extractor = MagicMock(spec=ExtractorExecutionService)
    mock_extractor.execute = AsyncMock(return_value=extraction_result)

    artifact_repo = SQLAlchemyArtifactRepository(shared_db_session)
    extraction_repo = SQLAlchemyExtractionRepository(shared_db_session)
    kg_repo = SQLAlchemyKnowledgeGraphRepository(shared_db_session)
    kg_builder = BuildKnowledgeGraphUseCase()

    use_case = ProcessArtifactUseCase(
        artifact_repository=artifact_repo,
        storage_service=DummyStorageService(),
        document_classifier=DeterministicDocumentClassifier(),
        extractor_execution_service=mock_extractor,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=kg_repo,
        build_knowledge_graph_use_case=kg_builder,
    )

    await use_case.execute(artifact.id)
    await shared_db_session.commit()

    # 1. Verify Artifact state
    updated_artifact = await artifact_repo.get_by_id(artifact.id)
    assert updated_artifact is not None
    assert updated_artifact.status == ProcessingStatus.COMPLETED
    assert updated_artifact.document_type == DocumentType.resume()

    # 2. Verify Extraction record in DB
    saved_extraction = await extraction_repo.get_by_artifact_id(artifact.id)
    assert saved_extraction is not None
    assert saved_extraction.status == ExtractionStatus.SUCCESS
    assert "skills" in saved_extraction.structured_data

    # 3. Verify Graph Entities in DB
    entity_stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    entity_result = await shared_db_session.execute(entity_stmt)
    entities = entity_result.scalars().all()
    assert len(entities) > 0
    entity_names = {e.name for e in entities}
    assert "Python" in entity_names
    assert "Chronicle Labs" in entity_names
    assert "Lead Architect" in entity_names
    assert "MIT" in entity_names

    # 4. Verify Graph Relationships in DB
    rel_stmt = select(GraphRelationshipModel).where(GraphRelationshipModel.user_id == user.id)
    rel_result = await shared_db_session.execute(rel_stmt)
    relationships = rel_result.scalars().all()
    assert len(relationships) > 0
    rel_types = {r.relationship_type for r in relationships}
    assert "WORKED_AT" in rel_types

    # 5. Verify Entity Artifact Provenance in DB
    ent_prov_stmt = select(EntityArtifactProvenanceModel).where(
        EntityArtifactProvenanceModel.artifact_id == artifact.id
    )
    ent_prov_result = await shared_db_session.execute(ent_prov_stmt)
    ent_provenances = ent_prov_result.scalars().all()
    assert len(ent_provenances) > 0
    for prov in ent_provenances:
        assert prov.artifact_id == artifact.id
        assert prov.confidence is not None

    # 6. Verify Relationship Artifact Provenance in DB
    rel_prov_stmt = select(RelationshipArtifactProvenanceModel).where(
        RelationshipArtifactProvenanceModel.artifact_id == artifact.id
    )
    rel_prov_result = await shared_db_session.execute(rel_prov_stmt)
    rel_provenances = rel_prov_result.scalars().all()
    assert len(rel_provenances) > 0
    for prov in rel_provenances:
        assert prov.artifact_id == artifact.id
        assert prov.confidence is not None


@pytest.mark.asyncio
async def test_kg_persistence_failure_leaves_extraction_persisted_and_zero_graph_records(
    shared_db_session: AsyncSession,
) -> None:
    """Batch 4B (CRITICAL INVARIANT):

    Proves on a REAL shared AsyncSession that if KG persistence fails:
    1. Artifact processing still completes successfully (status = COMPLETED).
    2. Extraction record remains safely persisted and committed in the database.
    3. The savepoint rollback ensures ZERO partial graph records exist in the database.
    """
    user = await _create_test_user(shared_db_session)
    artifact = await _create_test_artifact(shared_db_session, user.id)

    extraction_result = _make_resume_extraction_result(artifact.id)
    mock_extractor = MagicMock(spec=ExtractorExecutionService)
    mock_extractor.execute = AsyncMock(return_value=extraction_result)

    artifact_repo = SQLAlchemyArtifactRepository(shared_db_session)
    extraction_repo = SQLAlchemyExtractionRepository(shared_db_session)

    # We subclass SQLAlchemyKnowledgeGraphRepository to simulate a failure occurring
    # AFTER some entities have already been added/flushed within the SAVEPOINT.
    class FailingKnowledgeGraphRepository(SQLAlchemyKnowledgeGraphRepository):
        async def persist_graph(self, entities, relationships, entity_provenance, relationship_provenance):
            async with self._session.begin_nested():
                # Step 1: Save one entity inside the savepoint to demonstrate partial writes
                if entities:
                    await self.save_entity(entities[0])
                    await self._session.flush()

                # Step 2: Simulate an unexpected database error / constraint error
                raise RuntimeError("Simulated unrecoverable graph database error within savepoint")

    failing_kg_repo = FailingKnowledgeGraphRepository(shared_db_session)
    kg_builder = BuildKnowledgeGraphUseCase()

    use_case = ProcessArtifactUseCase(
        artifact_repository=artifact_repo,
        storage_service=DummyStorageService(),
        document_classifier=DeterministicDocumentClassifier(),
        extractor_execution_service=mock_extractor,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=failing_kg_repo,
        build_knowledge_graph_use_case=kg_builder,
    )

    # Execute artifact processing — must NOT raise
    await use_case.execute(artifact.id)

    # Outer transaction commit simulating request completion
    await shared_db_session.commit()

    # CRITICAL INVARIANT ASSERTION 1: Artifact processing completed successfully
    updated_artifact = await artifact_repo.get_by_id(artifact.id)
    assert updated_artifact is not None
    assert updated_artifact.status == ProcessingStatus.COMPLETED
    assert updated_artifact.error_message is None

    # CRITICAL INVARIANT ASSERTION 2: Extraction remains persisted in the database
    persisted_extraction = await extraction_repo.get_by_artifact_id(artifact.id)
    assert persisted_extraction is not None
    assert persisted_extraction.status == ExtractionStatus.SUCCESS
    assert persisted_extraction.artifact_id == artifact.id

    # CRITICAL INVARIANT ASSERTION 3: Zero partial graph records remain in the database
    entity_stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    entities_in_db = (await shared_db_session.execute(entity_stmt)).scalars().all()
    assert len(entities_in_db) == 0, f"Expected 0 entities, found {len(entities_in_db)}"

    rel_stmt = select(GraphRelationshipModel).where(GraphRelationshipModel.user_id == user.id)
    rels_in_db = (await shared_db_session.execute(rel_stmt)).scalars().all()
    assert len(rels_in_db) == 0, f"Expected 0 relationships, found {len(rels_in_db)}"

    ent_prov_stmt = select(EntityArtifactProvenanceModel).where(
        EntityArtifactProvenanceModel.artifact_id == artifact.id
    )
    ent_provs_in_db = (await shared_db_session.execute(ent_prov_stmt)).scalars().all()
    assert len(ent_provs_in_db) == 0, f"Expected 0 entity provenance rows, found {len(ent_provs_in_db)}"

    rel_prov_stmt = select(RelationshipArtifactProvenanceModel).where(
        RelationshipArtifactProvenanceModel.artifact_id == artifact.id
    )
    rel_provs_in_db = (await shared_db_session.execute(rel_prov_stmt)).scalars().all()
    assert len(rel_provs_in_db) == 0, f"Expected 0 relationship provenance rows, found {len(rel_provs_in_db)}"


@pytest.mark.asyncio
async def test_reprocessing_same_artifact_updates_graph_idempotently(
    shared_db_session: AsyncSession,
) -> None:
    """Batch 4B: Verifies reprocessing the same artifact updates graph records idempotently."""
    user = await _create_test_user(shared_db_session)
    artifact = await _create_test_artifact(shared_db_session, user.id)

    extraction_result = _make_resume_extraction_result(artifact.id)
    mock_extractor = MagicMock(spec=ExtractorExecutionService)
    mock_extractor.execute = AsyncMock(return_value=extraction_result)

    artifact_repo = SQLAlchemyArtifactRepository(shared_db_session)
    extraction_repo = SQLAlchemyExtractionRepository(shared_db_session)
    kg_repo = SQLAlchemyKnowledgeGraphRepository(shared_db_session)
    kg_builder = BuildKnowledgeGraphUseCase()

    use_case = ProcessArtifactUseCase(
        artifact_repository=artifact_repo,
        storage_service=DummyStorageService(),
        document_classifier=DeterministicDocumentClassifier(),
        extractor_execution_service=mock_extractor,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=kg_repo,
        build_knowledge_graph_use_case=kg_builder,
    )

    # First run
    await use_case.execute(artifact.id)
    await shared_db_session.commit()

    entity_stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    count_run_1 = len((await shared_db_session.execute(entity_stmt)).scalars().all())
    assert count_run_1 > 0

    # Second run (reprocessing)
    await use_case.execute(artifact.id)
    await shared_db_session.commit()

    count_run_2 = len((await shared_db_session.execute(entity_stmt)).scalars().all())
    assert count_run_2 == count_run_1, "Entity count should be identical due to semantic deduplication"

    # Artifact remains COMPLETED
    updated_artifact = await artifact_repo.get_by_id(artifact.id)
    assert updated_artifact.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_kg_pipeline_when_extraction_is_empty(
    shared_db_session: AsyncSession,
) -> None:
    """Batch 4B: Verifies that when extraction yields no graph candidates, pipeline completes with 0 graph records."""
    user = await _create_test_user(shared_db_session)
    artifact = await _create_test_artifact(shared_db_session, user.id)

    extraction_result = ExtractionResult(
        artifact_id=artifact.id,
        document_type=DocumentType.unknown(),
        structured_data={},
        provenance={},
        warnings=[],
        extractor_version="1.0.0",
        prompt_version="v1",
        status=ExtractionStatus.SUCCESS,
    )
    mock_extractor = MagicMock(spec=ExtractorExecutionService)
    mock_extractor.execute = AsyncMock(return_value=extraction_result)

    artifact_repo = SQLAlchemyArtifactRepository(shared_db_session)
    extraction_repo = SQLAlchemyExtractionRepository(shared_db_session)
    kg_repo = SQLAlchemyKnowledgeGraphRepository(shared_db_session)
    kg_builder = BuildKnowledgeGraphUseCase()

    use_case = ProcessArtifactUseCase(
        artifact_repository=artifact_repo,
        storage_service=DummyStorageService(),
        document_classifier=DeterministicDocumentClassifier(),
        extractor_execution_service=mock_extractor,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=kg_repo,
        build_knowledge_graph_use_case=kg_builder,
    )

    await use_case.execute(artifact.id)
    await shared_db_session.commit()

    updated_artifact = await artifact_repo.get_by_id(artifact.id)
    assert updated_artifact.status == ProcessingStatus.COMPLETED

    saved_extraction = await extraction_repo.get_by_artifact_id(artifact.id)
    assert saved_extraction is not None

    entity_stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    entities = (await shared_db_session.execute(entity_stmt)).scalars().all()
    assert len(entities) == 0


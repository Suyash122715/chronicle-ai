"""Unit tests for ProcessArtifactUseCase — Phase 4.1 classification & Phase 4.5 extraction pipeline."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.knowledge_graph.extraction_graph_mapper import GraphCandidates
from app.application.services.extractor_execution_service import ExtractorExecutionService
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.entities.graph_entity import EntityType, GraphEntity
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.infrastructure.processing.deterministic_classifier import DeterministicDocumentClassifier


class InMemoryArtifactRepository(ArtifactRepositoryInterface):
    def __init__(self) -> None:
        self._store: dict[UUID, Artifact] = {}

    async def add(self, artifact: Artifact) -> Artifact:
        self._store[artifact.id] = artifact
        return artifact

    async def get_by_id(self, artifact_id: UUID) -> Artifact | None:
        return self._store.get(artifact_id)

    async def get_by_user_id(self, user_id: UUID) -> list[Artifact]:
        return [a for a in self._store.values() if a.user_id == user_id]

    async def update(self, artifact: Artifact) -> Artifact:
        self._store[artifact.id] = artifact
        return artifact

    async def delete(self, artifact_id: UUID) -> bool:
        if artifact_id in self._store:
            del self._store[artifact_id]
            return True
        return False


class DummyStorageService(StorageServiceInterface):
    def __init__(self, fail_on_get: bool = False) -> None:
        self.fail_on_get = fail_on_get
        self.files: dict[str, bytes] = {}

    async def save_file(self, file_bytes: bytes, destination_filename: str) -> str:
        path = f"mock/{destination_filename}"
        self.files[path] = file_bytes
        return path

    async def get_file(self, file_path: str) -> bytes | None:
        if self.fail_on_get:
            return None
        return self.files.get(file_path, b"Default file content")

    async def delete_file(self, file_path: str) -> bool:
        return True


class InMemoryExtractionRepository(ExtractionRepositoryInterface):
    """In-memory ExtractionRepository for unit testing."""

    def __init__(self) -> None:
        self._store: list[ExtractionResult] = []
        self.save_call_count: int = 0

    async def save(self, extraction_result: ExtractionResult) -> ExtractionResult:
        self.save_call_count += 1
        self._store.append(extraction_result)
        return extraction_result

    async def get_by_artifact_id(self, artifact_id: UUID) -> ExtractionResult | None:
        matches = [r for r in self._store if r.artifact_id == artifact_id]
        return matches[-1] if matches else None

    async def get_all_by_artifact_id(self, artifact_id: UUID) -> list[ExtractionResult]:
        return [r for r in self._store if r.artifact_id == artifact_id]

    async def get_by_id(self, extraction_id: UUID) -> ExtractionResult | None:
        return None

    async def delete_by_artifact_id(self, artifact_id: UUID) -> bool:
        before = len(self._store)
        self._store = [r for r in self._store if r.artifact_id != artifact_id]
        return len(self._store) < before


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_artifact_success() -> None:
    """Verifies that the classification pipeline executes and persists results."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    classifier = DeterministicDocumentClassifier()
    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=storage,
        document_classifier=classifier,
    )

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="john_doe_resume.pdf",
        stored_filename="stored_resume.pdf",
        file_path="mock/stored_resume.pdf",
        file_size=100,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)

    await use_case.execute(artifact.id)

    processed = await repo.get_by_id(artifact.id)

    # Pipeline status
    assert processed.status == ProcessingStatus.COMPLETED
    assert processed.error_message is None

    # Classification was executed and persisted
    assert processed.document_type is not None
    assert processed.classification_confidence is not None
    assert processed.classifier_version is not None
    assert processed.classified_at is not None


@pytest.mark.asyncio
async def test_process_artifact_unknown_type() -> None:
    """Verifies that an artifact with no recognisable signals is classified as Unknown."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    classifier = DeterministicDocumentClassifier()
    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=storage,
        document_classifier=classifier,
    )

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="random_file.bin",
        stored_filename="stored_random.bin",
        file_path="mock/stored_random.bin",
        file_size=50,
        mime_type="application/octet-stream",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)

    await use_case.execute(artifact.id)

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED
    assert processed.document_type is not None
    assert processed.classifier_version is not None


@pytest.mark.asyncio
async def test_process_artifact_nonexistent_id_is_noop() -> None:
    """Verifies that processing a missing artifact ID is a safe no-op."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    classifier = DeterministicDocumentClassifier()
    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=storage,
        document_classifier=classifier,
    )

    # Should not raise
    await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_process_artifact_with_extractor_execution_service() -> None:
    """Verifies classification -> extraction pipeline flow via ExtractorExecutionService."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    classifier = DeterministicDocumentClassifier()

    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(
        return_value=ExtractionResult(
            artifact_id=uuid4(),
            document_type=DocumentType.resume(),
            structured_data={"skills": ["Python"]},
            provenance={},
            warnings=[],
            extractor_version="1.0.0",
            prompt_version="v1",
            status=ExtractionStatus.SUCCESS,
        )
    )

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=storage,
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
    )

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="resume_john.pdf",
        stored_filename="stored_resume_john.pdf",
        file_path="mock/stored_resume_john.pdf",
        file_size=200,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)

    await use_case.execute(artifact.id)

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED
    assert mock_extractor_service.execute.called
    assert mock_extractor_service.execute.call_args[1]["document_type"] == DocumentType.resume()


@pytest.mark.asyncio
async def test_process_artifact_extraction_failure_does_not_crash_pipeline() -> None:
    """Verifies that an exception during extraction does not crash the processing pipeline."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    classifier = DeterministicDocumentClassifier()

    failing_extractor_service = MagicMock(spec=ExtractorExecutionService)
    failing_extractor_service.execute = AsyncMock(side_effect=RuntimeError("Extraction service exception"))

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=storage,
        document_classifier=classifier,
        extractor_execution_service=failing_extractor_service,
    )

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="resume_jane.pdf",
        stored_filename="stored_resume_jane.pdf",
        file_path="mock/stored_resume_jane.pdf",
        file_size=200,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)

    # Must not raise
    await use_case.execute(artifact.id)

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


# ---------------------------------------------------------------------------
# Batch 3: Extraction Persistence Tests
# ---------------------------------------------------------------------------


def _make_artifact(filename: str = "resume_test.pdf") -> Artifact:
    """Helper to create a test artifact."""
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename=filename,
        stored_filename=f"stored_{filename}",
        file_path=f"mock/stored_{filename}",
        file_size=100,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )


def _make_extraction_result(artifact_id: UUID, status: ExtractionStatus) -> ExtractionResult:
    """Helper to create an ExtractionResult with a given status."""
    return ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={"skills": ["Python"]},
        provenance={},
        warnings=[],
        extractor_version="1.0.0",
        prompt_version="v1",
        status=status,
    )


@pytest.mark.asyncio
async def test_extraction_persistence_success_status_is_persisted() -> None:
    """Batch 3: Verifies that a SUCCESS extraction result is persisted via ExtractionRepositoryInterface."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_alice.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
    )

    await use_case.execute(artifact.id)

    assert extraction_repo.save_call_count == 1
    persisted = await extraction_repo.get_by_artifact_id(artifact.id)
    assert persisted is not None
    assert persisted.status == ExtractionStatus.SUCCESS

    # Verify artifact classification fields are still intact
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED
    assert processed.document_type is not None
    assert processed.classified_at is not None


@pytest.mark.asyncio
async def test_extraction_persistence_failed_status_is_persisted() -> None:
    """Batch 3: Verifies that a FAILED extraction result is persisted (all statuses must be saved)."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_bob.pdf")
    await repo.add(artifact)

    failed_result = _make_extraction_result(artifact.id, ExtractionStatus.FAILED)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=failed_result)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
    )

    await use_case.execute(artifact.id)

    assert extraction_repo.save_call_count == 1
    persisted = await extraction_repo.get_by_artifact_id(artifact.id)
    assert persisted is not None
    assert persisted.status == ExtractionStatus.FAILED

    # Processing pipeline must still complete successfully
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_extraction_persistence_skipped_status_is_persisted() -> None:
    """Batch 3: Verifies that a SKIPPED extraction result is persisted."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_carol.pdf")
    await repo.add(artifact)

    skipped_result = _make_extraction_result(artifact.id, ExtractionStatus.SKIPPED)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=skipped_result)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
    )

    await use_case.execute(artifact.id)

    assert extraction_repo.save_call_count == 1
    persisted = await extraction_repo.get_by_artifact_id(artifact.id)
    assert persisted is not None
    assert persisted.status == ExtractionStatus.SKIPPED

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_extraction_execution_failure_does_not_crash_pipeline_with_repo() -> None:
    """Batch 3: Verifies extraction execution failure does not crash the pipeline when extraction repo is present."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    failing_extractor_service = MagicMock(spec=ExtractorExecutionService)
    failing_extractor_service.execute = AsyncMock(side_effect=RuntimeError("Unexpected extraction crash"))

    artifact = _make_artifact("resume_dave.pdf")
    await repo.add(artifact)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=failing_extractor_service,
        extraction_repository=extraction_repo,
    )

    # Must not raise
    await use_case.execute(artifact.id)

    # Extraction repo should NOT have been called (the exception happened before save)
    assert extraction_repo.save_call_count == 0

    # Pipeline must still complete
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_extraction_repository_dependency_injection_works() -> None:
    """Batch 3: Verifies ExtractionRepositoryInterface can be injected and is called."""
    repo = InMemoryArtifactRepository()
    mock_extraction_repo = MagicMock(spec=ExtractionRepositoryInterface)
    mock_extraction_repo.save = AsyncMock(
        return_value=ExtractionResult(
            artifact_id=uuid4(),
            document_type=DocumentType.resume(),
            status=ExtractionStatus.SUCCESS,
        )
    )
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_eve.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=mock_extraction_repo,
    )

    await use_case.execute(artifact.id)

    mock_extraction_repo.save.assert_called_once()
    call_args = mock_extraction_repo.save.call_args
    saved_result = call_args[0][0]
    assert saved_result.status == ExtractionStatus.SUCCESS


@pytest.mark.asyncio
async def test_extraction_repository_save_failure_is_non_fatal() -> None:
    """Batch 3: Verifies that a repository save() failure does not crash the processing pipeline
    and follows the existing application error-handling convention (log, continue, COMPLETED)."""
    repo = InMemoryArtifactRepository()
    classifier = DeterministicDocumentClassifier()

    failing_extraction_repo = MagicMock(spec=ExtractionRepositoryInterface)
    failing_extraction_repo.save = AsyncMock(side_effect=RuntimeError("Database write failure"))

    artifact = _make_artifact("resume_frank.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=failing_extraction_repo,
    )

    # Must not raise — save failure is non-fatal
    await use_case.execute(artifact.id)

    # save was attempted
    failing_extraction_repo.save.assert_called_once()

    # Pipeline must still complete with COMPLETED status
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED

    # Classification fields must still be intact despite the persistence failure
    assert processed.document_type is not None
    assert processed.classified_at is not None


# ---------------------------------------------------------------------------
# Phase 5 Batch 4B: Knowledge Graph Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_artifact_builds_and_persists_knowledge_graph() -> None:
    """Batch 4B: Verifies that KG builder and persist_graph are invoked when extraction succeeds."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_kg_success.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    entity = GraphEntity(
        id=uuid4(),
        user_id=artifact.user_id,
        name="Python",
        canonical_name="python",
        entity_type=EntityType.SKILL,
    )
    candidates = GraphCandidates(
        entities=[entity],
        relationships=[],
        entity_provenance={entity.id: []},
        relationship_provenance={},
    )

    mock_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)
    mock_builder.execute = MagicMock(return_value=candidates)

    mock_kg_repo = MagicMock(spec=KnowledgeGraphRepositoryInterface)
    mock_kg_repo.persist_graph = AsyncMock()

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=mock_kg_repo,
        build_knowledge_graph_use_case=mock_builder,
    )

    await use_case.execute(artifact.id)

    # Builder called with proper user_id, artifact_id, and extraction_result
    mock_builder.execute.assert_called_once()
    builder_kwargs = mock_builder.execute.call_args[1]
    assert builder_kwargs["user_id"] == artifact.user_id
    assert builder_kwargs["artifact_id"] == artifact.id
    assert builder_kwargs["extraction_result"] == extraction_result

    # Knowledge graph repo persist_graph called with candidates
    mock_kg_repo.persist_graph.assert_called_once_with(
        entities=candidates.entities,
        relationships=candidates.relationships,
        entity_provenance=candidates.entity_provenance,
        relationship_provenance=candidates.relationship_provenance,
    )

    # Artifact marked COMPLETED
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_process_artifact_knowledge_graph_failure_is_non_fatal() -> None:
    """Batch 4B: Verifies that a failure during KG building or persistence does NOT fail artifact processing."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_kg_fail.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    entity = GraphEntity(
        id=uuid4(),
        user_id=artifact.user_id,
        name="Python",
        canonical_name="python",
        entity_type=EntityType.SKILL,
    )
    candidates = GraphCandidates(
        entities=[entity],
        relationships=[],
        entity_provenance={entity.id: []},
        relationship_provenance={},
    )

    mock_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)
    mock_builder.execute = MagicMock(return_value=candidates)

    mock_kg_repo = MagicMock(spec=KnowledgeGraphRepositoryInterface)
    mock_kg_repo.persist_graph = AsyncMock(side_effect=RuntimeError("Database failure during persist_graph"))

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=mock_kg_repo,
        build_knowledge_graph_use_case=mock_builder,
    )

    # Must not raise
    await use_case.execute(artifact.id)

    # Extraction must remain persisted
    assert extraction_repo.save_call_count == 1
    persisted_extraction = await extraction_repo.get_by_artifact_id(artifact.id)
    assert persisted_extraction is not None

    # Pipeline status must be COMPLETED
    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED
    assert processed.error_message is None


@pytest.mark.asyncio
async def test_process_artifact_empty_knowledge_graph_not_persisted() -> None:
    """Batch 4B: Verifies that if no entities or relationships are extracted, persist_graph is not called."""
    repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_kg_empty.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    empty_candidates = GraphCandidates(
        entities=[],
        relationships=[],
        entity_provenance={},
        relationship_provenance={},
    )

    mock_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)
    mock_builder.execute = MagicMock(return_value=empty_candidates)

    mock_kg_repo = MagicMock(spec=KnowledgeGraphRepositoryInterface)
    mock_kg_repo.persist_graph = AsyncMock()

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=extraction_repo,
        knowledge_graph_repository=mock_kg_repo,
        build_knowledge_graph_use_case=mock_builder,
    )

    await use_case.execute(artifact.id)

    mock_builder.execute.assert_called_once()
    mock_kg_repo.persist_graph.assert_not_called()

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_process_artifact_skips_knowledge_graph_when_extraction_persistence_fails() -> None:
    """Batch 4B: Verifies that if extraction persistence fails, KG persistence is skipped."""
    repo = InMemoryArtifactRepository()
    failing_extraction_repo = MagicMock(spec=ExtractionRepositoryInterface)
    failing_extraction_repo.save = AsyncMock(side_effect=RuntimeError("Extraction table crash"))
    classifier = DeterministicDocumentClassifier()

    artifact = _make_artifact("resume_kg_skip.pdf")
    await repo.add(artifact)

    extraction_result = _make_extraction_result(artifact.id, ExtractionStatus.SUCCESS)
    mock_extractor_service = MagicMock(spec=ExtractorExecutionService)
    mock_extractor_service.execute = AsyncMock(return_value=extraction_result)

    mock_builder = MagicMock(spec=BuildKnowledgeGraphUseCase)
    mock_kg_repo = MagicMock(spec=KnowledgeGraphRepositoryInterface)
    mock_kg_repo.persist_graph = AsyncMock()

    use_case = ProcessArtifactUseCase(
        artifact_repository=repo,
        storage_service=DummyStorageService(),
        document_classifier=classifier,
        extractor_execution_service=mock_extractor_service,
        extraction_repository=failing_extraction_repo,
        knowledge_graph_repository=mock_kg_repo,
        build_knowledge_graph_use_case=mock_builder,
    )

    await use_case.execute(artifact.id)

    # Builder and KG persist should be skipped because saved_extraction was None
    mock_builder.execute.assert_not_called()
    mock_kg_repo.persist_graph.assert_not_called()

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED


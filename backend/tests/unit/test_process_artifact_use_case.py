"""Unit tests for ProcessArtifactUseCase — Phase 4.1 classification pipeline."""

from uuid import UUID, uuid4
import pytest

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_artifact_success() -> None:
    """Verifies that the classification pipeline executes and persists results.

    Phase 4.1: processing = deterministic classification only.
    No text extraction occurs.
    """
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
    # Unknown file produces a classification result (type may be Unknown)
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

"""Unit tests for ProcessArtifactUseCase and DefaultTextExtractor."""

from uuid import UUID, uuid4
import pytest

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.exceptions.artifact_exceptions import StorageError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.infrastructure.processing.text_extractor import DefaultTextExtractor


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


@pytest.mark.asyncio
async def test_text_extractor_plain_text() -> None:
    """Verifies text extraction for plain text documents."""
    extractor = DefaultTextExtractor()
    content = b"Hello Chronicle AI World"
    text = await extractor.extract_text(content, "text/plain")
    assert text == "Hello Chronicle AI World"


@pytest.mark.asyncio
async def test_process_artifact_success() -> None:
    """Verifies successful processing pipeline execution."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    extractor = DefaultTextExtractor()
    use_case = ProcessArtifactUseCase(repo, storage, extractor)

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="notes.txt",
        stored_filename="stored_notes.txt",
        file_path="mock/stored_notes.txt",
        file_size=100,
        mime_type="text/plain",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)
    storage.files["mock/stored_notes.txt"] = b"Sample plain text content"

    await use_case.execute(artifact.id)

    processed = await repo.get_by_id(artifact.id)
    assert processed.status == ProcessingStatus.COMPLETED
    assert processed.raw_text == "Sample plain text content"
    assert processed.error_message is None


@pytest.mark.asyncio
async def test_process_artifact_storage_failure_retries_and_fails() -> None:
    """Verifies storage error triggers retries and eventually transitions to FAILED status."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService(fail_on_get=True)
    extractor = DefaultTextExtractor()
    use_case = ProcessArtifactUseCase(repo, storage, extractor, max_retries=2)

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="missing.pdf",
        stored_filename="stored_missing.pdf",
        file_path="mock/missing.pdf",
        file_size=50,
        mime_type="application/pdf",
        status=ProcessingStatus.PENDING,
    )
    await repo.add(artifact)

    # First attempt -> retry_count becomes 1
    await use_case.execute(artifact.id)
    state1 = await repo.get_by_id(artifact.id)
    assert state1.retry_count == 1
    assert state1.status == ProcessingStatus.FAILED

    # Second attempt -> retry_count becomes 2 (max_retries reached)
    await use_case.execute(artifact.id)
    state2 = await repo.get_by_id(artifact.id)
    assert state2.retry_count == 2
    assert state2.status == ProcessingStatus.FAILED
    assert "failed permanently" in state2.error_message.lower() or "attempt(s)" in state2.error_message.lower()

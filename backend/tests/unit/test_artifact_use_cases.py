"""Unit tests for Artifact Use Cases (Upload, List, Get, Delete)."""

from uuid import UUID, uuid4
import pytest

from app.application.artifacts.delete.delete_artifact_use_case import DeleteArtifactUseCase
from app.application.artifacts.get.get_artifact_use_case import GetArtifactUseCase
from app.application.artifacts.list.list_artifacts_use_case import ListArtifactsUseCase
from app.application.artifacts.upload.upload_artifact_use_case import UploadArtifactUseCase
from app.config import settings
from app.domain.entities.artifact import Artifact
from app.domain.exceptions.artifact_exceptions import (
    ArtifactNotFoundError,
    FileTooLargeError,
    UnsupportedMediaTypeError,
)
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface


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
    def __init__(self) -> None:
        self.saved_files: dict[str, bytes] = {}

    async def save_file(self, file_bytes: bytes, destination_filename: str) -> str:
        path = f"mock_storage/{destination_filename}"
        self.saved_files[path] = file_bytes
        return path

    async def get_file(self, file_path: str) -> bytes | None:
        return self.saved_files.get(file_path)

    async def delete_file(self, file_path: str) -> bool:
        if file_path in self.saved_files:
            del self.saved_files[file_path]
            return True
        return False


@pytest.mark.asyncio
async def test_upload_artifact_success() -> None:
    """Verifies successful artifact upload."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    use_case = UploadArtifactUseCase(repo, storage)

    user_id = uuid4()
    content = b"PDF content"
    artifact = await use_case.execute(
        user_id=user_id,
        filename="resume.pdf",
        file_bytes=content,
        mime_type="application/pdf",
    )

    assert artifact.user_id == user_id
    assert artifact.filename == "resume.pdf"
    assert artifact.file_size == len(content)
    assert artifact.mime_type == "application/pdf"
    assert len(storage.saved_files) == 1


@pytest.mark.asyncio
async def test_upload_artifact_exceeds_max_size_raises_error() -> None:
    """Verifies file size limit check raises FileTooLargeError."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    use_case = UploadArtifactUseCase(repo, storage)

    large_bytes = b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1)
    with pytest.raises(FileTooLargeError):
        await use_case.execute(
            user_id=uuid4(),
            filename="large.pdf",
            file_bytes=large_bytes,
            mime_type="application/pdf",
        )


@pytest.mark.asyncio
async def test_upload_artifact_unsupported_mime_type_raises_error() -> None:
    """Verifies unsupported MIME type raises UnsupportedMediaTypeError."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    use_case = UploadArtifactUseCase(repo, storage)

    with pytest.raises(UnsupportedMediaTypeError):
        await use_case.execute(
            user_id=uuid4(),
            filename="script.exe",
            file_bytes=b"binary",
            mime_type="application/x-msdownload",
        )


@pytest.mark.asyncio
async def test_get_and_list_artifacts() -> None:
    """Verifies retrieval and ownership checking for get and list use cases."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    upload_uc = UploadArtifactUseCase(repo, storage)
    get_uc = GetArtifactUseCase(repo)
    list_uc = ListArtifactsUseCase(repo)

    user1_id = uuid4()
    user2_id = uuid4()

    art1 = await upload_uc.execute(user1_id, "doc1.pdf", b"data1", "application/pdf")
    art2 = await upload_uc.execute(user1_id, "doc2.pdf", b"data2", "application/pdf")
    art3 = await upload_uc.execute(user2_id, "doc3.pdf", b"data3", "application/pdf")

    # List
    user1_arts = await list_uc.execute(user1_id)
    assert len(user1_arts) == 2

    # Get owned artifact
    fetched = await get_uc.execute(user1_id, art1.id)
    assert fetched.id == art1.id

    # Get another user's artifact raises ArtifactNotFoundError
    with pytest.raises(ArtifactNotFoundError):
        await get_uc.execute(user1_id, art3.id)


@pytest.mark.asyncio
async def test_delete_artifact() -> None:
    """Verifies deletion of metadata and physical file."""
    repo = InMemoryArtifactRepository()
    storage = DummyStorageService()
    upload_uc = UploadArtifactUseCase(repo, storage)
    delete_uc = DeleteArtifactUseCase(repo, storage)

    user_id = uuid4()
    art = await upload_uc.execute(user_id, "file.pdf", b"data", "application/pdf")

    result = await delete_uc.execute(user_id, art.id)
    assert result is True
    assert len(storage.saved_files) == 0
    assert await repo.get_by_id(art.id) is None

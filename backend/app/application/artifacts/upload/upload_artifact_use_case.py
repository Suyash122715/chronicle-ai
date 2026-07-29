"""Upload Artifact Use Case implementation."""

from pathlib import Path
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from app.config import settings
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.exceptions.artifact_exceptions import FileTooLargeError, UnsupportedMediaTypeError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.background_job_service import BackgroundJobServiceInterface
from app.domain.interfaces.storage_service import StorageServiceInterface


class UploadArtifactUseCase:
    """Application use case for validating, storing, and persisting an uploaded artifact.

    Enforces business rules:
    - File size validation (<= MAX_UPLOAD_SIZE_BYTES).
    - MIME type validation (in ALLOWED_MIME_TYPES).
    - Unique filename generation on disk.
    - Association of artifact metadata with authenticated user ID.
    - Cleanup of stored file if database persistence fails.
    - Immediate return with status=PENDING, delegating processing to background service.
    """

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        storage_service: StorageServiceInterface,
        background_job_service: BackgroundJobServiceInterface | None = None,
        process_task: Callable[[UUID], Awaitable[None]] | None = None,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service
        self._background_job_service = background_job_service
        self._process_task = process_task

    async def execute(
        self,
        user_id: UUID,
        filename: str,
        file_bytes: bytes,
        mime_type: str,
    ) -> Artifact:
        """Executes artifact upload workflow and enqueues background processing.

        Returns immediately with status PENDING.
        """
        # 1. Validate file size
        file_size = len(file_bytes)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise FileTooLargeError(f"File size exceeds maximum allowed limit of {max_mb}MB.")

        # 2. Validate MIME type
        normalized_mime = mime_type.lower().strip()
        if normalized_mime not in [t.lower() for t in settings.ALLOWED_MIME_TYPES]:
            raise UnsupportedMediaTypeError(f"Media type '{mime_type}' is not supported.")

        # 3. Generate unique stored filename preserving original extension
        ext = Path(filename).suffix
        stored_filename = f"{uuid4()}{ext}"

        # 4. Save file to storage
        file_path = await self._storage_service.save_file(file_bytes, stored_filename)

        # 5. Build Artifact domain entity with initial status PENDING
        artifact = Artifact(
            user_id=user_id,
            filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=normalized_mime,
            status=ProcessingStatus.PENDING,
        )

        # 6. Persist metadata to database (with storage rollback on failure)
        try:
            created_artifact = await self._artifact_repository.add(artifact)
        except Exception:
            await self._storage_service.delete_file(file_path)
            raise

        # 7. Enqueue background processing if job service and task are provided
        if self._background_job_service is not None and self._process_task is not None:
            self._background_job_service.enqueue_job(self._process_task, created_artifact.id)

        return created_artifact

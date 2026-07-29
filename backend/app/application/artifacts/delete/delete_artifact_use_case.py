"""Delete Artifact Use Case implementation."""

from uuid import UUID

from app.domain.exceptions.artifact_exceptions import ArtifactNotFoundError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface


class DeleteArtifactUseCase:
    """Application use case for deleting an artifact and its underlying stored file."""

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        storage_service: StorageServiceInterface,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_service = storage_service

    async def execute(self, user_id: UUID, artifact_id: UUID) -> bool:
        """Executes artifact deletion workflow.

        1. Retrieves artifact metadata to verify existence and ownership.
        2. Deletes stored file from physical storage.
        3. Deletes artifact record from database.

        Raises:
            ArtifactNotFoundError: If artifact does not exist or belongs to another user.
        """
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None or artifact.user_id != user_id:
            raise ArtifactNotFoundError()

        # Delete physical file from storage
        await self._storage_service.delete_file(artifact.file_path)

        # Delete metadata record from repository
        return await self._artifact_repository.delete(artifact_id)

"""Get Artifact Use Case implementation."""

from uuid import UUID

from app.domain.entities.artifact import Artifact
from app.domain.exceptions.artifact_exceptions import ArtifactNotFoundError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface


class GetArtifactUseCase:
    """Application use case for retrieving a specific artifact owned by the authenticated user."""

    def __init__(self, artifact_repository: ArtifactRepositoryInterface) -> None:
        self._artifact_repository = artifact_repository

    async def execute(self, user_id: UUID, artifact_id: UUID) -> Artifact:
        """Retrieves an artifact by ID and verifies ownership.

        Raises:
            ArtifactNotFoundError: If artifact does not exist or belongs to another user.
        """
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None or artifact.user_id != user_id:
            raise ArtifactNotFoundError()

        return artifact

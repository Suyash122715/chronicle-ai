"""List Artifacts Use Case implementation."""

from uuid import UUID

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface


class ListArtifactsUseCase:
    """Application use case for retrieving all artifacts owned by a specific user."""

    def __init__(self, artifact_repository: ArtifactRepositoryInterface) -> None:
        self._artifact_repository = artifact_repository

    async def execute(self, user_id: UUID) -> list[Artifact]:
        """Retrieves all artifacts for the specified user ID."""
        return await self._artifact_repository.get_by_user_id(user_id)

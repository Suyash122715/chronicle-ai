"""Artifact repository interface definition."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.artifact import Artifact


class ArtifactRepositoryInterface(ABC):
    """Abstract interface defining persistence operations for Artifact domain entities."""

    @abstractmethod
    async def add(self, artifact: Artifact) -> Artifact:
        """Persists a new artifact domain entity to storage."""
        pass

    @abstractmethod
    async def get_by_id(self, artifact_id: UUID) -> Artifact | None:
        """Retrieves an artifact by its unique identifier."""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Artifact]:
        """Retrieves all artifacts owned by a specific user."""
        pass

    @abstractmethod
    async def update(self, artifact: Artifact) -> Artifact:
        """Updates an existing artifact entity's state and processing results in storage."""
        pass

    @abstractmethod
    async def delete(self, artifact_id: UUID) -> bool:
        """Deletes an artifact record by its unique identifier.

        Returns:
            bool: True if deleted, False if record did not exist.
        """
        pass

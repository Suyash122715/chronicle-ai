"""Artifact Extraction repository interface definition."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.value_objects.extraction_result import ExtractionResult


class ExtractionRepositoryInterface(ABC):
    """Abstract interface defining persistence operations for ExtractionResult domain value objects."""

    @abstractmethod
    async def save(self, extraction_result: ExtractionResult) -> ExtractionResult:
        """Persists an ExtractionResult domain value object to storage and returns the persisted result."""
        pass

    @abstractmethod
    async def get_by_artifact_id(self, artifact_id: UUID) -> ExtractionResult | None:
        """Retrieves the latest extraction result for a specific artifact ID, if one exists."""
        pass

    @abstractmethod
    async def get_all_by_artifact_id(self, artifact_id: UUID) -> list[ExtractionResult]:
        """Retrieves all extraction results for a specific artifact ID ordered by created_at DESC."""
        pass

    @abstractmethod
    async def get_by_id(self, extraction_id: UUID) -> ExtractionResult | None:
        """Retrieves an extraction result by its unique extraction record ID."""
        pass

    @abstractmethod
    async def delete_by_artifact_id(self, artifact_id: UUID) -> bool:
        """Deletes all extraction records associated with a specific artifact ID.

        Returns:
            bool: True if any records were deleted, False otherwise.
        """
        pass

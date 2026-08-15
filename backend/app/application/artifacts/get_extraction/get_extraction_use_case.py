"""Get Extraction Use Case implementation."""

from uuid import UUID

from app.domain.exceptions.artifact_exceptions import ArtifactNotFoundError, ExtractionNotFoundError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.value_objects.extraction_result import ExtractionResult


class GetExtractionUseCase:
    """Application use case for retrieving an extraction result for an artifact owned by the user."""

    def __init__(
        self,
        artifact_repository: ArtifactRepositoryInterface,
        extraction_repository: ExtractionRepositoryInterface,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._extraction_repository = extraction_repository

    async def execute(self, user_id: UUID, artifact_id: UUID) -> ExtractionResult:
        """Retrieves the latest extraction result for an artifact owned by the authenticated user.

        Raises:
            ArtifactNotFoundError: If artifact does not exist or belongs to another user.
            ExtractionNotFoundError: If artifact exists but has no extraction result.
        """
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None or artifact.user_id != user_id:
            raise ArtifactNotFoundError()

        extraction = await self._extraction_repository.get_by_artifact_id(artifact_id)
        if extraction is None:
            raise ExtractionNotFoundError()

        return extraction

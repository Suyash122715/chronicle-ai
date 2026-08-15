"""SQLAlchemy 2 implementation of ExtractionRepositoryInterface."""

from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.db.models.artifact_extraction_model import ArtifactExtractionModel


class SQLAlchemyExtractionRepository(ExtractionRepositoryInterface):
    """Concrete repository using SQLAlchemy 2 async sessions to persist extraction results."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, extraction_result: ExtractionResult) -> ExtractionResult:
        """Persists an extraction result record to the database."""
        model = ArtifactExtractionModel.from_domain(extraction_result)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def get_by_artifact_id(self, artifact_id: UUID) -> ExtractionResult | None:
        """Retrieves the most recent extraction result for an artifact ID."""
        stmt = (
            select(ArtifactExtractionModel)
            .where(ArtifactExtractionModel.artifact_id == artifact_id)
            .order_by(ArtifactExtractionModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all_by_artifact_id(self, artifact_id: UUID) -> list[ExtractionResult]:
        """Retrieves all extraction records for an artifact ID ordered newest to oldest."""
        stmt = (
            select(ArtifactExtractionModel)
            .where(ArtifactExtractionModel.artifact_id == artifact_id)
            .order_by(ArtifactExtractionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_id(self, extraction_id: UUID) -> ExtractionResult | None:
        """Retrieves an extraction record by its primary key ID."""
        stmt = select(ArtifactExtractionModel).where(ArtifactExtractionModel.id == extraction_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def delete_by_artifact_id(self, artifact_id: UUID) -> bool:
        """Deletes all extraction records for a given artifact ID."""
        stmt = delete(ArtifactExtractionModel).where(ArtifactExtractionModel.artifact_id == artifact_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return bool(result.rowcount is not None and result.rowcount > 0)

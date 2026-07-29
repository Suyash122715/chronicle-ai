"""SQLAlchemy 2 implementation of ArtifactRepositoryInterface."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.infrastructure.db.models.artifact_model import ArtifactModel


class SQLAlchemyArtifactRepository(ArtifactRepositoryInterface):
    """Concrete repository using SQLAlchemy 2 async sessions to persist artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, artifact: Artifact) -> Artifact:
        """Persists a new artifact entity to the database."""
        model = ArtifactModel.from_domain(artifact)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def get_by_id(self, artifact_id: UUID) -> Artifact | None:
        """Retrieves an artifact by unique ID."""
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_user_id(self, user_id: UUID) -> list[Artifact]:
        """Retrieves all artifacts belonging to a given user ID ordered by created_at DESC."""
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.user_id == user_id)
            .order_by(ArtifactModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def update(self, artifact: Artifact) -> Artifact:
        """Updates an existing artifact entity's state in storage."""
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            model = ArtifactModel.from_domain(artifact)
            self._session.add(model)
        else:
            model.status = artifact.status.value
            model.raw_text = artifact.raw_text
            model.error_message = artifact.error_message
            model.retry_count = artifact.retry_count
            model.updated_at = artifact.updated_at

        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def delete(self, artifact_id: UUID) -> bool:
        """Deletes an artifact record from the database."""
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

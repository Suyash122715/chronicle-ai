"""SQLAlchemy 2 implementation of UserRepositoryInterface."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.db.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepositoryInterface):
    """Concrete repository using async SQLAlchemy 2 session for User persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        """Persists a User domain entity to the PostgreSQL/SQLAlchemy database."""
        model = UserModel.from_domain(user)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model.to_domain()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieves a user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a user by normalized email address."""
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def exists_by_email(self, email: str) -> bool:
        """Checks whether a user with the specified email exists."""
        stmt = select(UserModel.id).where(UserModel.email == email.lower().strip())
        result = await self._session.execute(stmt)
        return result.first() is not None

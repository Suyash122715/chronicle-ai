"""User repository interface definition."""

from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities.user import User


class UserRepositoryInterface(ABC):
    """Abstract interface defining persistence operations for User domain entities.
    
    The domain layer depends on this interface; concrete database implementations in the
    infrastructure layer fulfill this contract.
    """

    @abstractmethod
    async def add(self, user: User) -> User:
        """Persists a new user domain entity to storage."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieves a user by unique identifier."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a user by normalized email address."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Checks if a user with the given email already exists in storage."""
        pass

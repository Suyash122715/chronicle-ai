"""Unit tests for RegisterUserUseCase."""

from uuid import UUID, uuid4
import pytest

from app.application.authentication.register.register_user_use_case import RegisterUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    UserAlreadyExistsError,
    InvalidEmailFormatError,
    PasswordTooWeakError,
)
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_service import PasswordService


class InMemoryUserRepository(UserRepositoryInterface):
    """In-memory user repository mock for isolated unit testing."""

    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}
        self.emails: set[str] = set()

    async def add(self, user: User) -> User:
        self.users[user.id] = user
        self.emails.add(user.email.lower())
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        clean = email.lower()
        for u in self.users.values():
            if u.email.lower() == clean:
                return u
        return None

    async def exists_by_email(self, email: str) -> bool:
        return email.lower() in self.emails


@pytest.fixture
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def password_service() -> PasswordService:
    return PasswordService()


@pytest.fixture
def use_case(repo: InMemoryUserRepository, password_service: PasswordService) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repository=repo, password_service=password_service)


@pytest.mark.asyncio
async def test_register_user_success(use_case: RegisterUserUseCase, repo: InMemoryUserRepository, password_service: PasswordService) -> None:
    """Verifies successful user registration with valid credentials and Argon2 password hashing."""
    user = await use_case.execute(
        email="test.user@example.com",
        password="SecurePassword123!",
        full_name="Test User",
    )

    assert user.email == "test.user@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.password_hash.startswith("$argon2id$")
    assert password_service.verify_password("SecurePassword123!", user.password_hash) is True

    # Check persistence in repository
    assert await repo.exists_by_email("test.user@example.com") is True


@pytest.mark.asyncio
async def test_register_user_duplicate_email(use_case: RegisterUserUseCase, repo: InMemoryUserRepository) -> None:
    """Verifies that registering with an existing email raises UserAlreadyExistsError."""
    await use_case.execute(
        email="existing@example.com",
        password="Password123!",
        full_name="First User",
    )

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await use_case.execute(
            email="existing@example.com",
            password="AnotherPassword123!",
            full_name="Second User",
        )

    assert "existing@example.com" in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_user_invalid_email_format(use_case: RegisterUserUseCase) -> None:
    """Verifies that invalid email formats raise InvalidEmailFormatError."""
    with pytest.raises(InvalidEmailFormatError):
        await use_case.execute(
            email="not-a-valid-email",
            password="Password123!",
            full_name="Invalid Email User",
        )


@pytest.mark.asyncio
async def test_register_user_password_too_short(use_case: RegisterUserUseCase) -> None:
    """Verifies that passwords under 8 characters raise PasswordTooWeakError."""
    with pytest.raises(PasswordTooWeakError):
        await use_case.execute(
            email="shortpass@example.com",
            password="123",
            full_name="Short Password User",
        )

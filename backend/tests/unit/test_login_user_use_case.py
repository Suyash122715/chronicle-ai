"""Unit tests for LoginUserUseCase."""

import uuid
from datetime import datetime, timezone
import pytest

from app.application.authentication.login.login_user_use_case import LoginUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidCredentialsError
from app.domain.interfaces.token_service import TokenPayload, TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_service import PasswordService


class InMemoryUserRepository(UserRepositoryInterface):
    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    async def add(self, user: User) -> User:
        self._store[user.email] = user
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((u for u in self._store.values() if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return self._store.get(email.lower().strip())

    async def exists_by_email(self, email: str) -> bool:
        return email.lower().strip() in self._store


class DummyTokenService(TokenServiceInterface):
    def create_access_token(self, subject: str) -> str:
        return f"mock_token_for_{subject}"

    def decode_access_token(self, token: str) -> TokenPayload:
        return TokenPayload(subject="test_sub", expires_at=datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_login_user_success() -> None:
    """Verifies successful login returning token."""
    repo = InMemoryUserRepository()
    password_service = PasswordService()
    token_service = DummyTokenService()
    use_case = LoginUserUseCase(repo, password_service, token_service)

    raw_password = "StrongPassword123!"
    hashed_password = password_service.hash_password(raw_password)
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        email="testuser@example.com",
        password_hash=hashed_password,
        full_name="Test User",
        is_active=True,
    )
    await repo.add(user)

    result = await use_case.execute(email=" TESTUSER@example.com ", password=raw_password)
    assert result.access_token == f"mock_token_for_{user_id}"
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_user_wrong_email_raises_invalid_credentials() -> None:
    """Verifies that non-existent email raises InvalidCredentialsError."""
    repo = InMemoryUserRepository()
    password_service = PasswordService()
    token_service = DummyTokenService()
    use_case = LoginUserUseCase(repo, password_service, token_service)

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await use_case.execute(email="nonexistent@example.com", password="Password123!")

    assert exc_info.value.message == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_user_wrong_password_raises_invalid_credentials() -> None:
    """Verifies that wrong password raises InvalidCredentialsError."""
    repo = InMemoryUserRepository()
    password_service = PasswordService()
    token_service = DummyTokenService()
    use_case = LoginUserUseCase(repo, password_service, token_service)

    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        password_hash=password_service.hash_password("CorrectPassword123!"),
        full_name="User",
        is_active=True,
    )
    await repo.add(user)

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await use_case.execute(email="user@example.com", password="WrongPassword123!")

    assert exc_info.value.message == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_user_inactive_raises_invalid_credentials() -> None:
    """Verifies that inactive user raises InvalidCredentialsError."""
    repo = InMemoryUserRepository()
    password_service = PasswordService()
    token_service = DummyTokenService()
    use_case = LoginUserUseCase(repo, password_service, token_service)

    raw_password = "Password123!"
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        password_hash=password_service.hash_password(raw_password),
        full_name="Inactive User",
        is_active=False,
    )
    await repo.add(user)

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await use_case.execute(email="inactive@example.com", password=raw_password)

    assert exc_info.value.message == "Invalid email or password."

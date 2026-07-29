"""Unit tests for get_token_payload and get_current_user dependencies."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user, get_token_payload
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidTokenError
from app.domain.interfaces.token_service import TokenPayload, TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface


class InMemoryUserRepository(UserRepositoryInterface):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, User] = {}

    async def add(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email.lower().strip()), None)

    async def exists_by_email(self, email: str) -> bool:
        return any(u.email == email.lower().strip() for u in self._store.values())


class DummyTokenService(TokenServiceInterface):
    def create_access_token(self, subject: str) -> str:
        return f"token_{subject}"

    def decode_access_token(self, token: str) -> TokenPayload:
        if token == "expired_token":
            raise InvalidTokenError("Access token has expired.")
        if token == "malformed_token":
            raise InvalidTokenError("Access token is invalid.")
        subject = token.replace("token_", "")
        return TokenPayload(subject=subject, expires_at=datetime.now(timezone.utc))


def test_get_token_payload_missing_credentials_raises_invalid_token() -> None:
    """Missing Bearer credentials raises InvalidTokenError."""
    token_service = DummyTokenService()
    with pytest.raises(InvalidTokenError) as exc_info:
        get_token_payload(credentials=None, token_service=token_service)

    assert "credentials were not provided" in str(exc_info.value)


def test_get_token_payload_valid_credentials() -> None:
    """Valid Bearer credentials returns decoded TokenPayload."""
    token_service = DummyTokenService()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_123")
    payload = get_token_payload(credentials=creds, token_service=token_service)
    assert payload.subject == "123"


@pytest.mark.asyncio
async def test_get_current_user_success() -> None:
    """Valid user ID in payload returns active User entity."""
    repo = InMemoryUserRepository()
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="active@example.com",
        password_hash="hash",
        full_name="Active User",
        is_active=True,
    )
    await repo.add(user)

    payload = TokenPayload(subject=str(user_id), expires_at=datetime.now(timezone.utc))
    current_user = await get_current_user(payload=payload, user_repository=repo)
    assert current_user.id == user_id
    assert current_user.email == "active@example.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_uuid_subject_raises_invalid_token() -> None:
    """Non-UUID subject in payload raises InvalidTokenError."""
    repo = InMemoryUserRepository()
    payload = TokenPayload(subject="not-a-uuid", expires_at=datetime.now(timezone.utc))

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(payload=payload, user_repository=repo)

    assert "Invalid user ID in token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_user_not_found_raises_invalid_token() -> None:
    """User ID not found in database raises InvalidTokenError."""
    repo = InMemoryUserRepository()
    payload = TokenPayload(subject=str(uuid.uuid4()), expires_at=datetime.now(timezone.utc))

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(payload=payload, user_repository=repo)

    assert "account not found or inactive" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_user_inactive_raises_invalid_token() -> None:
    """Inactive user account raises InvalidTokenError."""
    repo = InMemoryUserRepository()
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="inactive@example.com",
        password_hash="hash",
        full_name="Inactive User",
        is_active=False,
    )
    await repo.add(user)

    payload = TokenPayload(subject=str(user_id), expires_at=datetime.now(timezone.utc))

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(payload=payload, user_repository=repo)

    assert "account not found or inactive" in str(exc_info.value)

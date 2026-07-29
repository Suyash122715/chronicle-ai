"""Integration tests for POST /api/v1/auth/login endpoint."""

import pytest
from httpx import AsyncClient

from app.dependencies import get_password_service, get_token_service, get_user_repository
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.jwt_token_service import JWTTokenService
from app.infrastructure.security.password_service import PasswordService


class InMemoryUserRepository(UserRepositoryInterface):
    """In-memory repository replacing database session for integration testing."""

    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    async def add(self, user: User) -> User:
        self._store[user.email] = user
        return user

    async def get_by_id(self, user_id) -> User | None:
        return next((u for u in self._store.values() if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return self._store.get(email.lower().strip())

    async def exists_by_email(self, email: str) -> bool:
        return email.lower().strip() in self._store


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client_with_overrides(async_client: AsyncClient) -> AsyncClient:
    """Overrides DB dependencies with in-memory implementations for isolated tests."""
    from app.main import app

    repo = InMemoryUserRepository()
    app.dependency_overrides[get_user_repository] = lambda: repo
    app.dependency_overrides[get_password_service] = lambda: PasswordService()
    app.dependency_overrides[get_token_service] = lambda: JWTTokenService()

    yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_success(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/login - Valid user login returns 200 OK and JWT access token."""
    # First register user
    reg_response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "StrongPassword123!",
            "full_name": "Login User",
        },
    )
    assert reg_response.status_code == 201

    # Now login with registered credentials
    login_response = await async_client_with_overrides.post(
        "/api/v1/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/login - Wrong password returns 401 Unauthorized."""
    await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong_pass@example.com",
            "password": "CorrectPassword123!",
            "full_name": "User",
        },
    )

    login_response = await async_client_with_overrides.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong_pass@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/login - Non-existent email returns 401 Unauthorized."""
    login_response = await async_client_with_overrides.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_invalid_email_format_returns_422(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/login - Invalid email format returns 422 Unprocessable Entity."""
    login_response = await async_client_with_overrides.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-email-format",
            "password": "Password123!",
        },
    )

    assert login_response.status_code == 422

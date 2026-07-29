"""Integration tests for GET /api/v1/users/me protected endpoint."""

import uuid
import pytest
from httpx import AsyncClient

from app.dependencies import get_password_service, get_token_service, get_user_repository
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.jwt_token_service import JWTTokenService
from app.infrastructure.security.password_service import PasswordService


class InMemoryUserRepository(UserRepositoryInterface):
    """In-memory repository for integration testing."""

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
async def test_get_me_success(async_client_with_overrides: AsyncClient) -> None:
    """GET /api/v1/users/me - Valid Bearer token returns 200 OK and user profile."""
    # 1. Register user
    reg_response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "me_test@example.com",
            "password": "StrongPassword123!",
            "full_name": "Me User",
        },
    )
    assert reg_response.status_code == 201

    # 2. Login user to get token
    login_response = await async_client_with_overrides.post(
        "/api/v1/auth/login",
        json={
            "email": "me_test@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. Call GET /users/me with Bearer token
    me_response = await async_client_with_overrides.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    body = me_response.json()
    assert body["email"] == "me_test@example.com"
    assert body["full_name"] == "Me User"
    assert body["is_active"] is True
    assert "id" in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_get_me_missing_token_returns_401(async_client_with_overrides: AsyncClient) -> None:
    """GET /api/v1/users/me - Missing Authorization header returns 401 Unauthorized."""
    response = await async_client_with_overrides.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


@pytest.mark.asyncio
async def test_get_me_malformed_token_returns_401(async_client_with_overrides: AsyncClient) -> None:
    """GET /api/v1/users/me - Malformed Bearer token returns 401 Unauthorized."""
    response = await async_client_with_overrides.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer malformed.invalid.token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token is invalid."

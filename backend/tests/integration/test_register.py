"""Integration tests for POST /api/v1/auth/register endpoint."""

import pytest
from httpx import AsyncClient

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserAlreadyExistsError
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_service import PasswordService
from app.dependencies import get_user_repository, get_password_service


# ---------------------------------------------------------------------------
# In-memory repository override used for integration tests (no DB required)
# ---------------------------------------------------------------------------

class InMemoryUserRepository(UserRepositoryInterface):
    """In-memory repository that replaces SQLAlchemy for integration testing."""

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

    yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_success(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/register - Valid payload returns HTTP 201 and user info."""
    response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "User registered successfully."
    assert body["user"]["email"] == "newuser@example.com"
    assert body["user"]["full_name"] == "New User"
    assert body["user"]["is_active"] is True
    assert "id" in body["user"]
    assert "password_hash" not in body["user"]


@pytest.mark.asyncio
async def test_register_user_duplicate_email_returns_409(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/register - Duplicate email returns HTTP 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "full_name": "Original User",
    }

    first = await async_client_with_overrides.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={**payload, "full_name": "Duplicate User"},
    )
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


@pytest.mark.asyncio
async def test_register_user_invalid_email_returns_422(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/register - Invalid email format returns HTTP 422 Unprocessable Entity."""
    response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
            "full_name": "Bad Email User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_short_password_returns_422(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/register - Password under 8 chars returns HTTP 422 Unprocessable Entity."""
    response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "abc",
            "full_name": "Short Password User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_missing_field_returns_422(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/auth/register - Missing full_name returns HTTP 422 Unprocessable Entity."""
    response = await async_client_with_overrides.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 422

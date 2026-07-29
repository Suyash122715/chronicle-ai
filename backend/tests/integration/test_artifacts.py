"""Integration tests for Artifact Management API endpoints (/api/v1/artifacts)."""

import io
import tempfile
import uuid
import pytest
from httpx import AsyncClient

from app.config import settings
from app.dependencies import (
    get_artifact_repository,
    get_password_service,
    get_storage_service,
    get_token_service,
    get_user_repository,
)
from app.domain.entities.artifact import Artifact
from app.domain.entities.user import User
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.jwt_token_service import JWTTokenService
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.storage.local_storage_service import LocalStorageService


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


class InMemoryArtifactRepository(ArtifactRepositoryInterface):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Artifact] = {}

    async def add(self, artifact: Artifact) -> Artifact:
        self._store[artifact.id] = artifact
        return artifact

    async def get_by_id(self, artifact_id: uuid.UUID) -> Artifact | None:
        return self._store.get(artifact_id)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[Artifact]:
        return [a for a in self._store.values() if a.user_id == user_id]

    async def update(self, artifact: Artifact) -> Artifact:
        self._store[artifact.id] = artifact
        return artifact

    async def delete(self, artifact_id: uuid.UUID) -> bool:
        if artifact_id in self._store:
            del self._store[artifact_id]
            return True
        return False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client_with_overrides(async_client: AsyncClient) -> AsyncClient:
    """Overrides DB and storage dependencies with isolated in-memory implementations."""
    from app.main import app

    user_repo = InMemoryUserRepository()
    artifact_repo = InMemoryArtifactRepository()

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(storage_dir=tmpdir)

        app.dependency_overrides[get_user_repository] = lambda: user_repo
        app.dependency_overrides[get_artifact_repository] = lambda: artifact_repo
        app.dependency_overrides[get_storage_service] = lambda: storage
        app.dependency_overrides[get_password_service] = lambda: PasswordService()
        app.dependency_overrides[get_token_service] = lambda: JWTTokenService()

        yield async_client

        app.dependency_overrides.clear()


async def _get_auth_header(client: AsyncClient, email: str) -> dict[str, str]:
    """Helper to register, login, and return Authorization header."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!", "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_artifact_success(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/artifacts/upload - Uploads file and returns 201 Created with status=pending."""
    headers = await _get_auth_header(async_client_with_overrides, "uploader@example.com")

    files = {"file": ("test_resume.pdf", io.BytesIO(b"%PDF-1.4 sample content"), "application/pdf")}
    response = await async_client_with_overrides.post(
        "/api/v1/artifacts/upload",
        headers=headers,
        files=files,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Artifact uploaded successfully."
    assert body["artifact"]["filename"] == "test_resume.pdf"
    assert body["artifact"]["mime_type"] == "application/pdf"
    assert body["artifact"]["status"] in ["pending", "completed"]
    assert "id" in body["artifact"]


@pytest.mark.asyncio
async def test_upload_unsupported_media_type_returns_415(async_client_with_overrides: AsyncClient) -> None:
    """POST /api/v1/artifacts/upload - Unsupported MIME type returns 415."""
    headers = await _get_auth_header(async_client_with_overrides, "badmime@example.com")

    files = {"file": ("script.sh", io.BytesIO(b"#!/bin/bash"), "application/x-sh")}
    response = await async_client_with_overrides.post(
        "/api/v1/artifacts/upload",
        headers=headers,
        files=files,
    )

    assert response.status_code == 415
    assert "not supported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_get_and_delete_artifacts(async_client_with_overrides: AsyncClient) -> None:
    """Full lifecycle: upload -> list -> get -> delete artifact."""
    headers = await _get_auth_header(async_client_with_overrides, "lifecycle@example.com")

    # 1. Upload two files
    f1 = {"file": ("doc1.pdf", io.BytesIO(b"content 1"), "application/pdf")}
    f2 = {"file": ("doc2.txt", io.BytesIO(b"content 2"), "text/plain")}

    resp1 = await async_client_with_overrides.post("/api/v1/artifacts/upload", headers=headers, files=f1)
    resp2 = await async_client_with_overrides.post("/api/v1/artifacts/upload", headers=headers, files=f2)
    assert resp1.status_code == 201
    assert resp2.status_code == 201

    art1_id = resp1.json()["artifact"]["id"]

    # 2. List artifacts
    list_resp = await async_client_with_overrides.get("/api/v1/artifacts", headers=headers)
    assert list_resp.status_code == 200
    artifacts_list = list_resp.json()
    assert len(artifacts_list) == 2

    # 3. Get single artifact
    get_resp = await async_client_with_overrides.get(f"/api/v1/artifacts/{art1_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["filename"] == "doc1.pdf"

    # 4. Delete artifact
    del_resp = await async_client_with_overrides.delete(f"/api/v1/artifacts/{art1_id}", headers=headers)
    assert del_resp.status_code == 204

    # 5. Get deleted artifact returns 404
    get_deleted_resp = await async_client_with_overrides.get(f"/api/v1/artifacts/{art1_id}", headers=headers)
    assert get_deleted_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_artifact_of_other_user_returns_404(async_client_with_overrides: AsyncClient) -> None:
    """GET /api/v1/artifacts/{id} - Accessing another user's artifact returns 404 Not Found."""
    headers1 = await _get_auth_header(async_client_with_overrides, "user1@example.com")
    headers2 = await _get_auth_header(async_client_with_overrides, "user2@example.com")

    # User 1 uploads artifact
    files = {"file": ("private.pdf", io.BytesIO(b"user1 private content"), "application/pdf")}
    upload_resp = await async_client_with_overrides.post("/api/v1/artifacts/upload", headers=headers1, files=files)
    art_id = upload_resp.json()["artifact"]["id"]

    # User 2 tries to get User 1's artifact
    get_resp = await async_client_with_overrides.get(f"/api/v1/artifacts/{art_id}", headers=headers2)
    assert get_resp.status_code == 404

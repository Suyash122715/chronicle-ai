"""Integration tests for GET /api/v1/artifacts/{artifact_id}/extraction API endpoint."""

from datetime import datetime, timezone
import tempfile
import uuid
import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_artifact_repository,
    get_extraction_repository,
    get_password_service,
    get_storage_service,
    get_token_service,
    get_user_repository,
)
from app.domain.entities.artifact import Artifact
from app.domain.entities.user import User
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
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


class InMemoryExtractionRepository(ExtractionRepositoryInterface):
    def __init__(self) -> None:
        self._store: list[ExtractionResult] = []

    async def save(self, extraction_result: ExtractionResult) -> ExtractionResult:
        self._store.append(extraction_result)
        return extraction_result

    async def get_by_artifact_id(self, artifact_id: uuid.UUID) -> ExtractionResult | None:
        matching = [r for r in self._store if r.artifact_id == artifact_id]
        if not matching:
            return None
        return sorted(matching, key=lambda r: r.completed_at, reverse=True)[0]

    async def get_all_by_artifact_id(self, artifact_id: uuid.UUID) -> list[ExtractionResult]:
        matching = [r for r in self._store if r.artifact_id == artifact_id]
        return sorted(matching, key=lambda r: r.completed_at, reverse=True)

    async def get_by_id(self, extraction_id: uuid.UUID) -> ExtractionResult | None:
        for r in self._store:
            if getattr(r, "id", None) == extraction_id or r.artifact_id == extraction_id:
                return r
        return None

    async def delete_by_artifact_id(self, artifact_id: uuid.UUID) -> bool:
        initial_len = len(self._store)
        self._store = [r for r in self._store if r.artifact_id != artifact_id]
        return len(self._store) < initial_len


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def extraction_test_context(async_client: AsyncClient):
    """Provides isolated repositories for integration testing extraction GET endpoint."""
    from app.main import app

    user_repo = InMemoryUserRepository()
    artifact_repo = InMemoryArtifactRepository()
    extraction_repo = InMemoryExtractionRepository()

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(storage_dir=tmpdir)

        app.dependency_overrides[get_user_repository] = lambda: user_repo
        app.dependency_overrides[get_artifact_repository] = lambda: artifact_repo
        app.dependency_overrides[get_extraction_repository] = lambda: extraction_repo
        app.dependency_overrides[get_storage_service] = lambda: storage
        app.dependency_overrides[get_password_service] = lambda: PasswordService()
        app.dependency_overrides[get_token_service] = lambda: JWTTokenService()

        yield {
            "client": async_client,
            "user_repo": user_repo,
            "artifact_repo": artifact_repo,
            "extraction_repo": extraction_repo,
        }

        app.dependency_overrides.clear()


async def _create_user_and_artifact(
    client: AsyncClient,
    user_repo: InMemoryUserRepository,
    artifact_repo: InMemoryArtifactRepository,
    email: str,
    filename: str = "test_document.pdf",
) -> tuple[dict[str, str], uuid.UUID]:
    """Helper to register/login a user, seed an artifact record, and return (headers, artifact_id)."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!", "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = await user_repo.get_by_email(email)
    assert user is not None

    artifact_id = uuid.uuid4()
    artifact = Artifact(
        id=artifact_id,
        user_id=user.id,
        filename=filename,
        stored_filename=f"stored_{filename}",
        file_path=f"/storage/{filename}",
        file_size=1024,
        mime_type="application/pdf",
    )
    await artifact_repo.add(artifact)

    return headers, artifact_id


@pytest.mark.asyncio
async def test_1_authenticated_user_retrieves_extraction_successfully(extraction_test_context) -> None:
    """1. Authenticated user retrieves extraction successfully (200 OK)."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]
    extraction_repo = extraction_test_context["extraction_repo"]

    headers, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "user1_success@example.com")

    # Seed extraction result
    extraction = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={"full_name": "Alice Bob", "skills": ["Python", "FastAPI"]},
        provenance={"full_name": Provenance(artifact_id=artifact_id, evidence_snippet="Alice Bob", confidence="HIGH")},
        warnings=[],
        confidence=ConfidenceLevel.HIGH,
        extractor_version="1.0.0",
        prompt_version="v1",
        llm_metadata={"provider": "mock"},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status=ExtractionStatus.SUCCESS,
    )
    await extraction_repo.save(extraction)

    # Retrieve extraction
    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["artifact_id"] == str(artifact_id)
    assert body["status"] == "SUCCESS"
    assert body["structured_data"] == {"full_name": "Alice Bob", "skills": ["Python", "FastAPI"]}


@pytest.mark.asyncio
async def test_2_unauthenticated_request_rejected(extraction_test_context) -> None:
    """2. Unauthenticated request rejected (401 Unauthorized)."""
    client = extraction_test_context["client"]
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/artifacts/{random_id}/extraction")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_3_nonexistent_artifact_returns_404(extraction_test_context) -> None:
    """3. Nonexistent artifact returns 404 Not Found."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]

    headers, _ = await _create_user_and_artifact(client, user_repo, artifact_repo, "user_nonexistent@example.com")
    nonexistent_id = uuid.uuid4()

    response = await client.get(f"/api/v1/artifacts/{nonexistent_id}/extraction", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_4_another_users_artifact_cannot_be_accessed(extraction_test_context) -> None:
    """4. Another user's artifact cannot be accessed (returns 404 Not Found)."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]

    # User 1 (owner)
    _, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "owner@example.com")

    # User 2 (other user)
    headers_other, _ = await _create_user_and_artifact(client, user_repo, artifact_repo, "other_user@example.com")

    # Other user attempts to access extraction
    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers_other)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_5_artifact_without_extraction_returns_404(extraction_test_context) -> None:
    """5. Artifact exists but has no extraction result returns 404 Not Found."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]

    headers, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "no_extraction@example.com")

    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_6_success_extraction_response_contains_structured_data_provenance_and_status(extraction_test_context) -> None:
    """6. SUCCESS extraction response contains structured_data, provenance and status."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]
    extraction_repo = extraction_test_context["extraction_repo"]

    headers, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "user_success_details@example.com")

    extraction = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.certificate(),
        structured_data={"issuer": "AWS", "certificate_name": "Solutions Architect"},
        provenance={"issuer": Provenance(artifact_id=artifact_id, evidence_snippet="AWS", confidence="HIGH")},
        warnings=[],
        confidence=ConfidenceLevel.HIGH,
        extractor_version="CertificateExtractor",
        prompt_version="v1",
        llm_metadata={"provider": "gemini"},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status=ExtractionStatus.SUCCESS,
    )
    await extraction_repo.save(extraction)

    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["structured_data"] == {"issuer": "AWS", "certificate_name": "Solutions Architect"}
    assert "issuer" in body["provenance"]
    assert body["provenance"]["issuer"]["evidence_snippet"] == "AWS"
    assert body["extractor_version"] == "CertificateExtractor"
    assert body["prompt_version"] == "v1"


@pytest.mark.asyncio
async def test_7_failed_extraction_preserves_status_and_error_message(extraction_test_context) -> None:
    """7. FAILED extraction preserves status and error_message."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]
    extraction_repo = extraction_test_context["extraction_repo"]

    headers, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "user_failed@example.com")

    failed_extraction = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={},
        provenance={},
        warnings=["LLM call timed out"],
        confidence=ConfidenceLevel.LOW,
        extractor_version="ResumeExtractor",
        prompt_version="v1",
        llm_metadata={"provider": "gemini", "error": "timeout"},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status=ExtractionStatus.FAILED,
        error_message="LLM service failed to respond within timeout threshold.",
    )
    await extraction_repo.save(failed_extraction)

    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error_message"] == "LLM service failed to respond within timeout threshold."
    assert body["structured_data"] == {}


@pytest.mark.asyncio
async def test_8_skipped_extraction_preserves_status_and_error_message(extraction_test_context) -> None:
    """8. SKIPPED extraction preserves status and error_message."""
    client = extraction_test_context["client"]
    user_repo = extraction_test_context["user_repo"]
    artifact_repo = extraction_test_context["artifact_repo"]
    extraction_repo = extraction_test_context["extraction_repo"]

    headers, artifact_id = await _create_user_and_artifact(client, user_repo, artifact_repo, "user_skipped@example.com")

    skipped_extraction = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.unknown(),
        structured_data={},
        provenance={},
        warnings=["Unknown document type skipped"],
        confidence=ConfidenceLevel.LOW,
        extractor_version="UnknownExtractor",
        prompt_version="none",
        llm_metadata={},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status=ExtractionStatus.SKIPPED,
        error_message="Document classification unknown; extraction skipped.",
    )
    await extraction_repo.save(skipped_extraction)

    response = await client.get(f"/api/v1/artifacts/{artifact_id}/extraction", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SKIPPED"
    assert body["error_message"] == "Document classification unknown; extraction skipped."
    assert body["structured_data"] == {}

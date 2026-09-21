"""Integration tests for Career Intelligence API endpoints (/api/v1/intelligence)."""

from datetime import datetime, timezone
import tempfile
import uuid
import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_artifact_repository,
    get_db_session,
    get_knowledge_graph_repository,
    get_password_service,
    get_storage_service,
    get_token_service,
    get_user_repository,
)
from app.domain.entities.artifact import Artifact
from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.entities.user import User
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
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


class InMemoryKnowledgeGraphRepository(KnowledgeGraphRepositoryInterface):
    def __init__(self) -> None:
        self.entities: dict[uuid.UUID, GraphEntity] = {}
        self.relationships: dict[uuid.UUID, GraphRelationship] = {}
        self.entity_provenance: dict[uuid.UUID, list[GraphProvenance]] = {}
        self.relationship_provenance: dict[uuid.UUID, list[GraphProvenance]] = {}

    async def save_entity(
        self, entity: GraphEntity, provenance: GraphProvenance | None = None
    ) -> GraphEntity:
        canonical = canonicalize_name(entity.name)
        existing = next(
            (
                e for e in self.entities.values()
                if e.user_id == entity.user_id and e.entity_type == entity.entity_type and e.canonical_name == canonical
            ),
            None,
        )
        saved = existing if existing else entity
        if not existing:
            self.entities[entity.id] = entity
        if provenance:
            self.entity_provenance.setdefault(saved.id, []).append(provenance)
        return saved

    async def get_entity_by_id(self, entity_id: uuid.UUID) -> GraphEntity | None:
        return self.entities.get(entity_id)

    async def get_entity_by_canonical(
        self, user_id: uuid.UUID, entity_type: EntityType, canonical_name: str
    ) -> GraphEntity | None:
        canonical = canonicalize_name(canonical_name)
        return next(
            (
                e for e in self.entities.values()
                if e.user_id == user_id and e.entity_type == entity_type and e.canonical_name == canonical
            ),
            None,
        )

    async def list_entities_by_user(
        self, user_id: uuid.UUID, entity_type: EntityType | None = None
    ) -> list[GraphEntity]:
        res = [e for e in self.entities.values() if e.user_id == user_id]
        if entity_type:
            res = [e for e in res if e.entity_type == entity_type]
        return res

    async def save_relationship(
        self, relationship: GraphRelationship, provenance: GraphProvenance | None = None
    ) -> GraphRelationship:
        self.relationships[relationship.id] = relationship
        if provenance:
            self.relationship_provenance.setdefault(relationship.id, []).append(provenance)
        return relationship

    async def get_relationship_by_id(self, relationship_id: uuid.UUID) -> GraphRelationship | None:
        return self.relationships.get(relationship_id)

    async def get_user_graph(
        self, user_id: uuid.UUID, artifact_id: uuid.UUID | None = None, entity_type: EntityType | None = None
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        ents = [e for e in self.entities.values() if e.user_id == user_id]
        rels = [r for r in self.relationships.values() if r.user_id == user_id]
        return ents, rels

    async def delete_entity(self, entity_id: uuid.UUID) -> bool:
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
        return False

    async def delete_provenance_by_artifact_id(self, artifact_id: uuid.UUID) -> bool:
        return True

    async def persist_graph(
        self, entities: list[GraphEntity], relationships: list[GraphRelationship],
        entity_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        return entities, relationships

    async def get_provenance_for_entities(
        self, user_id: uuid.UUID, entity_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[GraphProvenance]]:
        return {eid: list(self.entity_provenance.get(eid, [])) for eid in entity_ids}

    async def get_provenance_for_relationships(
        self, user_id: uuid.UUID, relationship_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[GraphProvenance]]:
        return {rid: list(self.relationship_provenance.get(rid, [])) for rid in relationship_ids}

    async def get_skill_metric_profiles(self, user_id: uuid.UUID) -> list[SkillMetricProfile]:
        profiles = []
        for e in self.entities.values():
            if e.user_id == user_id and e.entity_type in (EntityType.SKILL, EntityType.TECHNOLOGY):
                prov_count = len({p.artifact_id for p in self.entity_provenance.get(e.id, [])})
                proj_count = len({
                    r.source_entity_id for r in self.relationships.values()
                    if r.target_entity_id == e.id and r.relationship_type == RelationshipType.USES
                    and self.entities.get(r.source_entity_id) and self.entities[r.source_entity_id].entity_type == EntityType.PROJECT
                })
                exp_count = len({
                    r.source_entity_id for r in self.relationships.values()
                    if r.target_entity_id == e.id and r.relationship_type == RelationshipType.USES
                    and self.entities.get(r.source_entity_id) and self.entities[r.source_entity_id].entity_type == EntityType.ROLE
                })
                cert_count = len({
                    r.source_entity_id for r in self.relationships.values()
                    if r.target_entity_id == e.id and r.relationship_type == RelationshipType.CERTIFIED_IN
                    and self.entities.get(r.source_entity_id) and self.entities[r.source_entity_id].entity_type == EntityType.CERTIFICATE
                })
                profiles.append(
                    SkillMetricProfile(
                        entity_id=e.id,
                        canonical_name=e.canonical_name,
                        entity_type=e.entity_type,
                        frequency=prov_count,
                        project_count=proj_count,
                        experience_count=exp_count,
                        certificate_count=cert_count,
                    )
                )
        return profiles

    async def rebuild_artifact_graph(
        self, user_id: uuid.UUID, artifact_id: uuid.UUID, fresh_entities: list[GraphEntity],
        fresh_relationships: list[GraphRelationship],
        entity_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        return fresh_entities, fresh_relationships

    async def rebuild_user_graph(self, user_id: uuid.UUID) -> None:
        pass


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def setup_intelligence_env(async_client: AsyncClient):
    """Overrides application dependencies with test state."""
    from app.main import app
    from unittest.mock import AsyncMock
    from sqlalchemy.ext.asyncio import AsyncSession

    user_repo = InMemoryUserRepository()
    artifact_repo = InMemoryArtifactRepository()
    kg_repo = InMemoryKnowledgeGraphRepository()

    mock_session = AsyncMock(spec=AsyncSession)
    async def _mock_get_db_session():
        yield mock_session

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(storage_dir=tmpdir)

        app.dependency_overrides[get_db_session] = _mock_get_db_session
        app.dependency_overrides[get_user_repository] = lambda: user_repo
        app.dependency_overrides[get_artifact_repository] = lambda: artifact_repo
        app.dependency_overrides[get_knowledge_graph_repository] = lambda: kg_repo
        app.dependency_overrides[get_storage_service] = lambda: storage
        app.dependency_overrides[get_password_service] = lambda: PasswordService()
        app.dependency_overrides[get_token_service] = lambda: JWTTokenService()

        yield {
            "client": async_client,
            "user_repo": user_repo,
            "artifact_repo": artifact_repo,
            "kg_repo": kg_repo,
        }

        app.dependency_overrides.clear()


async def _get_auth_header(client: AsyncClient, email: str = "intel_user@example.com") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!", "full_name": "Intel User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_scored_skills_endpoint(setup_intelligence_env: dict) -> None:
    """GET /api/v1/intelligence/skills returns scored competency list."""
    client: AsyncClient = setup_intelligence_env["client"]
    user_repo: InMemoryUserRepository = setup_intelligence_env["user_repo"]
    kg_repo: InMemoryKnowledgeGraphRepository = setup_intelligence_env["kg_repo"]

    headers = await _get_auth_header(client, "scorer@example.com")
    user = await user_repo.get_by_email("scorer@example.com")
    assert user is not None

    # Seed SKILL and TECHNOLOGY nodes for Python
    skill_py = await kg_repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Python"),
        provenance=GraphProvenance(artifact_id=uuid.uuid4(), confidence="HIGH"),
    )
    tech_py = await kg_repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.TECHNOLOGY, name="Python"),
        provenance=GraphProvenance(artifact_id=uuid.uuid4(), confidence="HIGH"),
    )

    # Add ROLE and PROJECT connected via USES
    role = await kg_repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Backend Lead"))
    proj = await kg_repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.PROJECT, name="API Service"))

    await kg_repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role.id, target_entity_id=skill_py.id, relationship_type=RelationshipType.USES)
    )
    await kg_repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=proj.id, target_entity_id=tech_py.id, relationship_type=RelationshipType.USES)
    )

    response = await client.get("/api/v1/intelligence/skills", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["canonical_name"] == "python"
    assert item["experience_count"] == 1
    assert item["project_count"] == 1
    assert item["tech_entity_id"] is not None


@pytest.mark.asyncio
async def test_get_summary_endpoint(setup_intelligence_env: dict) -> None:
    """GET /api/v1/intelligence/summary returns career insights summary."""
    client: AsyncClient = setup_intelligence_env["client"]
    headers = await _get_auth_header(client, "summary_user@example.com")

    response = await client.get("/api/v1/intelligence/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_competencies" in data
    assert "top_skills" in data
    assert "evidence_light_count" in data


@pytest.mark.asyncio
async def test_gap_analysis_endpoint_not_found(setup_intelligence_env: dict) -> None:
    """Verifies that /api/v1/intelligence/gap-analysis returns 404 (excluded from V1)."""
    client: AsyncClient = setup_intelligence_env["client"]
    headers = await _get_auth_header(client, "gap_user@example.com")

    response = await client.get("/api/v1/intelligence/gap-analysis", headers=headers)
    assert response.status_code == 404

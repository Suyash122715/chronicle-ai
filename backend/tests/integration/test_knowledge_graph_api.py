"""Integration tests for Knowledge Graph Query API endpoint (GET /api/v1/graph)."""

from datetime import datetime, timezone
import tempfile
import uuid
import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_artifact_repository,
    get_knowledge_graph_repository,
    get_password_service,
    get_storage_service,
    get_token_service,
    get_user_repository,
)
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.entities.user import User
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
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
        return self._store.pop(artifact_id, None) is not None


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
                e
                for e in self.entities.values()
                if e.user_id == entity.user_id
                and e.entity_type == entity.entity_type
                and e.canonical_name == canonical
            ),
            None,
        )
        if existing:
            saved = existing
        else:
            self.entities[entity.id] = entity
            saved = entity

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
                e
                for e in self.entities.values()
                if e.user_id == user_id
                and e.entity_type == entity_type
                and e.canonical_name == canonical
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
        self,
        user_id: uuid.UUID,
        artifact_id: uuid.UUID | None = None,
        entity_type: EntityType | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        ents = [e for e in self.entities.values() if e.user_id == user_id]

        if artifact_id is not None:
            valid_entity_ids = {
                eid
                for eid, prov_list in self.entity_provenance.items()
                if any(p.artifact_id == artifact_id for p in prov_list)
            }
            ents = [e for e in ents if e.id in valid_entity_ids]

        if entity_type is not None:
            ents = [e for e in ents if e.entity_type == entity_type]

        rels = [r for r in self.relationships.values() if r.user_id == user_id]
        if artifact_id is not None:
            valid_rel_ids = {
                rid
                for rid, prov_list in self.relationship_provenance.items()
                if any(p.artifact_id == artifact_id for p in prov_list)
            }
            rels = [r for r in rels if r.id in valid_rel_ids]

        if entity_type is not None and artifact_id is None:
            ent_ids = {e.id for e in ents}
            rels = [
                r
                for r in rels
                if r.source_entity_id in ent_ids and r.target_entity_id in ent_ids
            ]

        return ents, rels

    async def delete_entity(self, entity_id: uuid.UUID) -> bool:
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
        return False

    async def delete_provenance_by_artifact_id(self, artifact_id: uuid.UUID) -> bool:
        return True

    async def persist_graph(
        self,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
        entity_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[uuid.UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        return entities, relationships

    async def get_provenance_for_entities(
        self, user_id: uuid.UUID, entity_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[GraphProvenance]]:
        user_entity_ids = {
            e.id for e in self.entities.values() if e.user_id == user_id and e.id in entity_ids
        }
        return {
            eid: list(self.entity_provenance.get(eid, []))
            for eid in entity_ids
            if eid in user_entity_ids
        }

    async def get_provenance_for_relationships(
        self, user_id: uuid.UUID, relationship_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[GraphProvenance]]:
        user_rel_ids = {
            r.id
            for r in self.relationships.values()
            if r.user_id == user_id and r.id in relationship_ids
        }
        return {
            rid: list(self.relationship_provenance.get(rid, []))
            for rid in relationship_ids
            if rid in user_rel_ids
        }


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def setup_kg_api_env(async_client: AsyncClient):
    """Overrides application dependencies with test state."""
    from app.main import app

    user_repo = InMemoryUserRepository()
    artifact_repo = InMemoryArtifactRepository()
    kg_repo = InMemoryKnowledgeGraphRepository()

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(storage_dir=tmpdir)

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


async def _register_and_login(
    client: AsyncClient, user_repo: InMemoryUserRepository, email: str
) -> tuple[dict[str, str], uuid.UUID]:
    """Helper to register, login, and return auth headers along with user ID."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!", "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    user = await user_repo.get_by_email(email)
    assert user is not None
    return {"Authorization": f"Bearer {token}"}, user.id



@pytest.mark.asyncio
async def test_1_unauthenticated_request_rejected(setup_kg_api_env) -> None:
    """GET /api/v1/graph without Authorization header returns HTTP 401 Unauthorized."""
    client: AsyncClient = setup_kg_api_env["client"]
    resp = await client.get("/api/v1/graph")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_2_get_user_graph_empty_returns_200(setup_kg_api_env) -> None:
    """GET /api/v1/graph for new user with no graph returns 200 with zero nodes and edges."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    headers, _ = await _register_and_login(client, user_repo, "empty_user@example.com")

    resp = await client.get("/api/v1/graph", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_nodes"] == 0
    assert body["total_edges"] == 0
    assert body["nodes"] == []
    assert body["edges"] == []


@pytest.mark.asyncio
async def test_3_get_user_graph_returns_nodes_edges_and_provenance(setup_kg_api_env) -> None:
    """GET /api/v1/graph returns full knowledge graph including provenance citations."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    kg_repo: InMemoryKnowledgeGraphRepository = setup_kg_api_env["kg_repo"]
    artifact_repo: InMemoryArtifactRepository = setup_kg_api_env["artifact_repo"]

    headers, user_id = await _register_and_login(client, user_repo, "graph_user@example.com")

    artifact = await artifact_repo.add(
        Artifact(
            user_id=user_id,
            filename="resume.pdf",
            stored_filename="stored_resume.pdf",
            file_path="/tmp/test.pdf",
            file_size=2048,
            mime_type="application/pdf",
            status=ProcessingStatus.COMPLETED,
        )
    )

    prov = GraphProvenance(
        artifact_id=artifact.id,
        confidence="HIGH",
        evidence_snippet="Python developer at TechCorp",
        source_location="Page 1",
    )

    e1 = await kg_repo.save_entity(
        GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Python"),
        provenance=prov,
    )
    e2 = await kg_repo.save_entity(
        GraphEntity(user_id=user_id, entity_type=EntityType.COMPANY, name="TechCorp"),
        provenance=prov,
    )
    rel = await kg_repo.save_relationship(
        GraphRelationship(
            user_id=user_id,
            source_entity_id=e2.id,
            target_entity_id=e1.id,
            relationship_type=RelationshipType.USES,
            weight=1.5,
        ),
        provenance=prov,
    )

    resp = await client.get("/api/v1/graph", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_nodes"] == 2
    assert body["total_edges"] == 1

    node_names = {n["name"] for n in body["nodes"]}
    assert node_names == {"Python", "TechCorp"}

    # Verify provenance was enriched
    node_python = next(n for n in body["nodes"] if n["name"] == "Python")
    assert len(node_python["provenance"]) == 1
    assert node_python["provenance"][0]["artifact_id"] == str(artifact.id)
    assert node_python["provenance"][0]["evidence_snippet"] == "Python developer at TechCorp"
    assert node_python["provenance"][0]["confidence"] == "HIGH"

    edge = body["edges"][0]
    assert edge["relationship_type"] == "USES"
    assert edge["weight"] == 1.5
    assert len(edge["provenance"]) == 1


@pytest.mark.asyncio
async def test_4_get_user_graph_filtered_by_artifact_id(setup_kg_api_env) -> None:
    """GET /api/v1/graph?artifact_id=... returns only elements from that specific artifact."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    kg_repo: InMemoryKnowledgeGraphRepository = setup_kg_api_env["kg_repo"]
    artifact_repo: InMemoryArtifactRepository = setup_kg_api_env["artifact_repo"]

    headers, user_id = await _register_and_login(client, user_repo, "artifact_filter@example.com")

    art1 = await artifact_repo.add(
        Artifact(
            user_id=user_id,
            filename="art1.pdf",
            stored_filename="art1.pdf",
            file_path="/tmp/art1.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=ProcessingStatus.COMPLETED,
        )
    )
    art2 = await artifact_repo.add(
        Artifact(
            user_id=user_id,
            filename="art2.pdf",
            stored_filename="art2.pdf",
            file_path="/tmp/art2.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=ProcessingStatus.COMPLETED,
        )
    )

    prov1 = GraphProvenance(artifact_id=art1.id, confidence="HIGH")
    prov2 = GraphProvenance(artifact_id=art2.id, confidence="LOW")

    await kg_repo.save_entity(
        GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Rust"),
        provenance=prov1,
    )
    await kg_repo.save_entity(
        GraphEntity(user_id=user_id, entity_type=EntityType.COMPANY, name="Mozilla"),
        provenance=prov2,
    )

    # Filter to art1 only
    resp = await client.get(f"/api/v1/graph?artifact_id={art1.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_nodes"] == 1
    assert body["nodes"][0]["name"] == "Rust"


@pytest.mark.asyncio
async def test_5_get_user_graph_cross_user_artifact_returns_404(setup_kg_api_env) -> None:
    """GET /api/v1/graph?artifact_id=... with another user's artifact ID returns 404."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    artifact_repo: InMemoryArtifactRepository = setup_kg_api_env["artifact_repo"]

    headers_u1, _ = await _register_and_login(client, user_repo, "user1_iso@example.com")
    _, user2_id = await _register_and_login(client, user_repo, "user2_iso@example.com")

    # Artifact owned by user 2
    u2_art = await artifact_repo.add(
        Artifact(
            user_id=user2_id,
            filename="secret.pdf",
            stored_filename="secret.pdf",
            file_path="/tmp/secret.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=ProcessingStatus.COMPLETED,
        )
    )

    # User 1 queries User 2's artifact
    resp = await client.get(f"/api/v1/graph?artifact_id={u2_art.id}", headers=headers_u1)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Artifact not found."


@pytest.mark.asyncio
async def test_6_get_user_graph_nonexistent_artifact_returns_404(setup_kg_api_env) -> None:
    """GET /api/v1/graph?artifact_id=... with random UUID returns 404."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    headers, _ = await _register_and_login(client, user_repo, "nonexistent@example.com")

    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/graph?artifact_id={random_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_7_get_user_graph_filtered_by_entity_type(setup_kg_api_env) -> None:
    """GET /api/v1/graph?entity_type=SKILL returns only nodes matching SKILL type."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    kg_repo: InMemoryKnowledgeGraphRepository = setup_kg_api_env["kg_repo"]

    headers, user_id = await _register_and_login(client, user_repo, "type_filter@example.com")

    await kg_repo.save_entity(GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Java"))
    await kg_repo.save_entity(GraphEntity(user_id=user_id, entity_type=EntityType.ROLE, name="Architect"))

    resp = await client.get("/api/v1/graph?entity_type=skill", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_nodes"] == 1
    assert body["nodes"][0]["name"] == "Java"
    assert body["nodes"][0]["entity_type"] == "SKILL"


@pytest.mark.asyncio
async def test_8_get_user_graph_invalid_entity_type_returns_400(setup_kg_api_env) -> None:
    """GET /api/v1/graph?entity_type=INVALID returns 400 Bad Request."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    headers, _ = await _register_and_login(client, user_repo, "bad_type@example.com")

    resp = await client.get("/api/v1/graph?entity_type=NOT_A_TYPE", headers=headers)
    assert resp.status_code == 400
    assert "Invalid entity_type" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_9_get_user_graph_include_provenance_false(setup_kg_api_env) -> None:
    """GET /api/v1/graph?include_provenance=false omits provenance citations."""
    client: AsyncClient = setup_kg_api_env["client"]
    user_repo: InMemoryUserRepository = setup_kg_api_env["user_repo"]
    kg_repo: InMemoryKnowledgeGraphRepository = setup_kg_api_env["kg_repo"]
    artifact_repo: InMemoryArtifactRepository = setup_kg_api_env["artifact_repo"]

    headers, user_id = await _register_and_login(client, user_repo, "no_prov@example.com")


    artifact = await artifact_repo.add(
        Artifact(
            user_id=user_id,
            filename="test.pdf",
            stored_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=ProcessingStatus.COMPLETED,
        )
    )
    prov = GraphProvenance(artifact_id=artifact.id, confidence="HIGH")

    await kg_repo.save_entity(
        GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="C#"),
        provenance=prov,
    )

    resp = await client.get("/api/v1/graph?include_provenance=false", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_nodes"] == 1
    assert body["nodes"][0]["provenance"] == []

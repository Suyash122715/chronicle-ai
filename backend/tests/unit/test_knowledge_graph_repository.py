"""Unit tests for SQLAlchemyKnowledgeGraphRepository implementing KnowledgeGraphRepositoryInterface."""

from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.exceptions.graph_exceptions import GraphEntityNotFoundError
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.artifact_model import ArtifactModel
from app.infrastructure.db.models.entity_artifact_provenance_model import EntityArtifactProvenanceModel
from app.infrastructure.db.models.graph_entity_model import GraphEntityModel
from app.infrastructure.db.models.graph_relationship_model import GraphRelationshipModel
from app.infrastructure.db.models.relationship_artifact_provenance_model import RelationshipArtifactProvenanceModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.repositories.knowledge_graph_repository import SQLAlchemyKnowledgeGraphRepository


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated async SQLite database session for repository tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_test_user(session: AsyncSession, email: str | None = None) -> UserModel:
    """Helper to seed a valid user record."""
    user = UserModel(
        id=uuid4(),
        email=email or f"user_{uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw_dummy",
        full_name="Test User",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def _create_test_artifact(session: AsyncSession, user_id: UUID) -> ArtifactModel:
    """Helper to seed a valid artifact record."""
    artifact = ArtifactModel(
        id=uuid4(),
        user_id=user_id,
        filename="test_resume.pdf",
        stored_filename=f"{uuid4().hex}.pdf",
        file_path="/tmp/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status="PROCESSED",
    )
    session.add(artifact)
    await session.flush()
    return artifact


# -----------------------------------------------------------------------------
# Test 1: Create new entity
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_new_entity(db_session: AsyncSession) -> None:
    """Verifies that a new GraphEntity is persisted with properties and canonical_name."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    entity = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="  Python  ",
        properties={"level": "Advanced"},
    )

    saved = await repo.save_entity(entity)

    assert saved.id == entity.id
    assert saved.user_id == user.id
    assert saved.entity_type == EntityType.SKILL
    assert saved.name == "Python"
    assert saved.canonical_name == "python"
    assert saved.properties == {"level": "Advanced"}

    # Verify directly in database
    stmt = select(GraphEntityModel).where(GraphEntityModel.id == saved.id)
    res = await db_session.execute(stmt)
    model = res.scalar_one_or_none()
    assert model is not None
    assert model.canonical_name == "python"


# -----------------------------------------------------------------------------
# Test 2: Re-persist same semantic entity -> no duplicate (reuses DB ID)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_repersist_same_semantic_entity_no_duplicate(db_session: AsyncSession) -> None:
    """Verifies semantic resolution (user_id, entity_type, canonical_name) reuses existing DB entity ID."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # 1. First candidate entity
    candidate_1 = GraphEntity(
        id=uuid4(),
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="Python",
        properties={"source": "resume"},
    )
    saved_1 = await repo.save_entity(candidate_1)

    # 2. Second candidate entity with identical semantic identity but different ephemeral UUID
    candidate_2 = GraphEntity(
        id=uuid4(),  # Different candidate UUID
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="  python  ",  # Normalizes to 'python'
        properties={"proficiency": "expert"},
    )
    saved_2 = await repo.save_entity(candidate_2)

    # Invariant: Must reuse the first database entity's UUID
    assert saved_2.id == saved_1.id
    assert saved_2.id != candidate_2.id

    # Verify only 1 entity exists in DB for this user
    stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    res = await db_session.execute(stmt)
    all_entities = res.scalars().all()
    assert len(all_entities) == 1


# -----------------------------------------------------------------------------
# Test 3: Same entity name but different entity type -> separate entities
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_same_entity_name_different_entity_type_separate_entities(db_session: AsyncSession) -> None:
    """Verifies entities with the same name but different EntityType are kept separate."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    skill_python = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="Python",
    )
    tech_python = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.TECHNOLOGY,
        name="Python",
    )

    saved_skill = await repo.save_entity(skill_python)
    saved_tech = await repo.save_entity(tech_python)

    assert saved_skill.id != saved_tech.id
    assert saved_skill.entity_type == EntityType.SKILL
    assert saved_tech.entity_type == EntityType.TECHNOLOGY

    stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user.id)
    res = await db_session.execute(stmt)
    assert len(res.scalars().all()) == 2


# -----------------------------------------------------------------------------
# Test 4: Same canonical entity but different user -> separate entities
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_same_canonical_entity_different_user_separate_entities(db_session: AsyncSession) -> None:
    """Verifies user isolation: two users with identical canonical entities have isolated records."""
    user_a = await _create_test_user(db_session, "alice@example.com")
    user_b = await _create_test_user(db_session, "bob@example.com")
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    entity_a = GraphEntity(
        user_id=user_a.id,
        entity_type=EntityType.SKILL,
        name="Python",
    )
    entity_b = GraphEntity(
        user_id=user_b.id,
        entity_type=EntityType.SKILL,
        name="Python",
    )

    saved_a = await repo.save_entity(entity_a)
    saved_b = await repo.save_entity(entity_b)

    assert saved_a.id != saved_b.id
    assert saved_a.user_id == user_a.id
    assert saved_b.user_id == user_b.id


# -----------------------------------------------------------------------------
# Test 5: Entity properties update/merge behavior
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_entity_properties_update_merge_behavior(db_session: AsyncSession) -> None:
    """Verifies that re-persisting an existing entity merges its properties with existing properties."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # Initial persist
    initial_entity = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="Python",
        properties={"level": "Junior", "verified": False},
    )
    saved_initial = await repo.save_entity(initial_entity)
    assert saved_initial.properties == {"level": "Junior", "verified": False}

    # Re-persist with updated and new fields
    reprocessed_entity = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.SKILL,
        name="Python",
        properties={"level": "Senior", "years_experience": 5},
    )
    saved_updated = await repo.save_entity(reprocessed_entity)

    assert saved_updated.id == saved_initial.id
    # "level": "Junior" and "verified": False are preserved from first insertion (earliest-wins), "years_experience" is added
    assert saved_updated.properties == {
        "level": "Junior",
        "verified": False,
        "years_experience": 5,
    }


# -----------------------------------------------------------------------------
# Test 6: Create relationship
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_relationship(db_session: AsyncSession) -> None:
    """Verifies creating and persisting a valid relationship between two user entities."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    role = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Engineer"))
    company = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Acme"))

    relationship = GraphRelationship(
        user_id=user.id,
        source_entity_id=role.id,
        target_entity_id=company.id,
        relationship_type=RelationshipType.HELD_ROLE,
        weight=1.5,
        properties={"start_year": 2022},
    )

    saved_rel = await repo.save_relationship(relationship)

    assert saved_rel.id == relationship.id
    assert saved_rel.user_id == user.id
    assert saved_rel.source_entity_id == role.id
    assert saved_rel.target_entity_id == company.id
    assert saved_rel.relationship_type == RelationshipType.HELD_ROLE
    assert saved_rel.weight == 1.5
    assert saved_rel.properties == {"start_year": 2022}


# -----------------------------------------------------------------------------
# Test 7: Re-persist same relationship -> no duplicate
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_repersist_same_relationship_no_duplicate(db_session: AsyncSession) -> None:
    """Verifies relationship identity (user_id, source, target, rel_type) reuses DB ID and updates properties."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    skill = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Python"))
    proj = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.PROJECT, name="Chronicle"))

    rel_1 = GraphRelationship(
        id=uuid4(),
        user_id=user.id,
        source_entity_id=proj.id,
        target_entity_id=skill.id,
        relationship_type=RelationshipType.USES,
        weight=1.0,
        properties={"context": "backend"},
    )
    saved_1 = await repo.save_relationship(rel_1)

    rel_2 = GraphRelationship(
        id=uuid4(),  # Different ephemeral UUID
        user_id=user.id,
        source_entity_id=proj.id,
        target_entity_id=skill.id,
        relationship_type=RelationshipType.USES,
        weight=2.0,
        properties={"framework": "FastAPI"},
    )
    saved_2 = await repo.save_relationship(rel_2)

    assert saved_2.id == saved_1.id
    assert saved_2.weight == 2.0
    assert saved_2.properties == {"context": "backend", "framework": "FastAPI"}

    # Verify single relationship in DB
    stmt = select(GraphRelationshipModel).where(GraphRelationshipModel.user_id == user.id)
    res = await db_session.execute(stmt)
    assert len(res.scalars().all()) == 1


# -----------------------------------------------------------------------------
# Test 8: Relationship references resolved database entity IDs
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_relationship_references_resolved_database_entity_ids(db_session: AsyncSession) -> None:
    """Verifies that persist_graph remaps ephemeral mapper UUIDs to existing DB entity UUIDs."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # Pre-existing entities in DB
    db_entity_a = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Developer"))
    db_entity_b = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Google"))

    # Ephemeral candidate entities from a new extraction
    mapper_id_a = uuid4()
    mapper_id_b = uuid4()
    candidate_a = GraphEntity(id=mapper_id_a, user_id=user.id, entity_type=EntityType.ROLE, name="Developer")
    candidate_b = GraphEntity(id=mapper_id_b, user_id=user.id, entity_type=EntityType.COMPANY, name="Google")

    # Candidate relationship connecting ephemeral mapper IDs
    candidate_rel = GraphRelationship(
        user_id=user.id,
        source_entity_id=mapper_id_a,
        target_entity_id=mapper_id_b,
        relationship_type=RelationshipType.HELD_ROLE,
    )

    entities, relationships = await repo.persist_graph(
        entities=[candidate_a, candidate_b],
        relationships=[candidate_rel],
    )

    assert len(relationships) == 1
    persisted_rel = relationships[0]

    # Invariant: Must use the DATABASE entity IDs, not mapper IDs
    assert persisted_rel.source_entity_id == db_entity_a.id
    assert persisted_rel.target_entity_id == db_entity_b.id
    assert persisted_rel.source_entity_id != mapper_id_a
    assert persisted_rel.target_entity_id != mapper_id_b


# -----------------------------------------------------------------------------
# Test 9: Relationship cannot accidentally cross users
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_relationship_cannot_accidentally_cross_users(db_session: AsyncSession) -> None:
    """Verifies that attempting to persist a relationship referencing an entity of another user raises GraphEntityNotFoundError."""
    user_alice = await _create_test_user(db_session, "alice_cross@example.com")
    user_bob = await _create_test_user(db_session, "bob_cross@example.com")
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    alice_entity = await repo.save_entity(GraphEntity(user_id=user_alice.id, entity_type=EntityType.ROLE, name="Lead"))
    bob_entity = await repo.save_entity(GraphEntity(user_id=user_bob.id, entity_type=EntityType.COMPANY, name="Corp"))

    # Alice attempts to create relationship pointing to Bob's entity
    cross_rel = GraphRelationship(
        user_id=user_alice.id,
        source_entity_id=alice_entity.id,
        target_entity_id=bob_entity.id,
        relationship_type=RelationshipType.HELD_ROLE,
    )

    with pytest.raises(GraphEntityNotFoundError):
        await repo.save_relationship(cross_rel)

    # Bob attempts to create relationship pointing to Alice's entity
    cross_rel_bob = GraphRelationship(
        user_id=user_bob.id,
        source_entity_id=alice_entity.id,
        target_entity_id=bob_entity.id,
        relationship_type=RelationshipType.HELD_ROLE,
    )

    with pytest.raises(GraphEntityNotFoundError):
        await repo.save_relationship(cross_rel_bob)


# -----------------------------------------------------------------------------
# Test 10: Entity provenance creation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_entity_provenance_creation(db_session: AsyncSession) -> None:
    """Verifies saving an entity with provenance persists record to entity_artifact_provenance."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    prov = GraphProvenance(
        artifact_id=artifact.id,
        confidence="HIGH",
        evidence_snippet="AWS Solutions Architect Associate",
        source_location="page 1",
    )
    entity = GraphEntity(user_id=user.id, entity_type=EntityType.CERTIFICATE, name="AWS Solutions Architect")

    saved_entity = await repo.save_entity(entity, provenance=prov)

    stmt = select(EntityArtifactProvenanceModel).where(
        EntityArtifactProvenanceModel.entity_id == saved_entity.id,
        EntityArtifactProvenanceModel.artifact_id == artifact.id,
    )
    res = await db_session.execute(stmt)
    prov_record = res.scalar_one_or_none()

    assert prov_record is not None
    assert prov_record.user_id == user.id
    assert prov_record.confidence == "HIGH"
    assert prov_record.evidence["evidence_snippet"] == "AWS Solutions Architect Associate"


# -----------------------------------------------------------------------------
# Test 11: Entity provenance re-persistence -> no duplicate (entity_id, artifact_id)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_entity_provenance_repersistence_no_duplicate(db_session: AsyncSession) -> None:
    """Verifies reprocessing the same entity and artifact updates existing provenance row without duplicate."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    prov_1 = GraphProvenance(artifact_id=artifact.id, confidence="LOW", evidence_snippet="First snippet")
    entity_1 = GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Python")
    saved_entity_1 = await repo.save_entity(entity_1, provenance=prov_1)

    prov_2 = GraphProvenance(artifact_id=artifact.id, confidence="HIGH", evidence_snippet="Second snippet")
    entity_2 = GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Python")
    saved_entity_2 = await repo.save_entity(entity_2, provenance=prov_2)

    assert saved_entity_1.id == saved_entity_2.id

    stmt = select(EntityArtifactProvenanceModel).where(
        EntityArtifactProvenanceModel.entity_id == saved_entity_1.id,
        EntityArtifactProvenanceModel.artifact_id == artifact.id,
    )
    res = await db_session.execute(stmt)
    records = res.scalars().all()
    assert len(records) == 1
    assert records[0].confidence == "HIGH"
    assert records[0].evidence["evidence_snippet"] == "Second snippet"


# -----------------------------------------------------------------------------
# Test 12: Relationship provenance creation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_relationship_provenance_creation(db_session: AsyncSession) -> None:
    """Verifies saving a relationship with provenance persists to relationship_artifact_provenance."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    role = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Staff"))
    comp = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Meta"))

    prov = GraphProvenance(
        artifact_id=artifact.id,
        confidence="HIGH",
        evidence_snippet="Staff Software Engineer at Meta 2020-2024",
    )
    rel = GraphRelationship(
        user_id=user.id,
        source_entity_id=role.id,
        target_entity_id=comp.id,
        relationship_type=RelationshipType.HELD_ROLE,
    )

    saved_rel = await repo.save_relationship(rel, provenance=prov)

    stmt = select(RelationshipArtifactProvenanceModel).where(
        RelationshipArtifactProvenanceModel.relationship_id == saved_rel.id,
        RelationshipArtifactProvenanceModel.artifact_id == artifact.id,
    )
    res = await db_session.execute(stmt)
    record = res.scalar_one_or_none()

    assert record is not None
    assert record.user_id == user.id
    assert record.confidence == "HIGH"
    assert record.evidence["evidence_snippet"] == "Staff Software Engineer at Meta 2020-2024"


# -----------------------------------------------------------------------------
# Test 13: Relationship provenance re-persistence -> no duplicate
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_relationship_provenance_repersistence_no_duplicate(db_session: AsyncSession) -> None:
    """Verifies reprocessing a relationship for the same artifact updates row without duplicating."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    role = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Analyst"))
    inst = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.INSTITUTION, name="MIT"))

    prov_1 = GraphProvenance(artifact_id=artifact.id, confidence="LOW", evidence_snippet="MIT")
    rel_1 = GraphRelationship(
        user_id=user.id,
        source_entity_id=role.id,
        target_entity_id=inst.id,
        relationship_type=RelationshipType.STUDIED_AT,
    )
    saved_1 = await repo.save_relationship(rel_1, provenance=prov_1)

    prov_2 = GraphProvenance(artifact_id=artifact.id, confidence="HIGH", evidence_snippet="MIT Grad 2021")
    rel_2 = GraphRelationship(
        user_id=user.id,
        source_entity_id=role.id,
        target_entity_id=inst.id,
        relationship_type=RelationshipType.STUDIED_AT,
    )
    saved_2 = await repo.save_relationship(rel_2, provenance=prov_2)

    assert saved_1.id == saved_2.id

    stmt = select(RelationshipArtifactProvenanceModel).where(
        RelationshipArtifactProvenanceModel.relationship_id == saved_1.id,
        RelationshipArtifactProvenanceModel.artifact_id == artifact.id,
    )
    res = await db_session.execute(stmt)
    records = res.scalars().all()
    assert len(records) == 1
    assert records[0].confidence == "HIGH"
    assert records[0].evidence["evidence_snippet"] == "MIT Grad 2021"


# -----------------------------------------------------------------------------
# Test 14: Provenance updates on reprocessing
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_provenance_updates_on_reprocessing(db_session: AsyncSession) -> None:
    """Verifies that confidence, evidence snippet, and extraction_id update correctly upon reprocessing."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    extraction_1 = uuid4()
    prov_1 = GraphProvenance(
        artifact_id=artifact.id,
        extraction_id=extraction_1,
        confidence="LOW",
        evidence_snippet="Early extraction",
        source_location="loc 1",
    )
    entity = GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Docker")
    saved = await repo.save_entity(entity, provenance=prov_1)

    # Reprocess with updated extraction
    extraction_2 = uuid4()
    prov_2 = GraphProvenance(
        artifact_id=artifact.id,
        extraction_id=extraction_2,
        confidence="HIGH",
        evidence_snippet="Updated extraction",
        source_location="loc 2",
    )
    await repo.save_entity(entity, provenance=prov_2)

    stmt = select(EntityArtifactProvenanceModel).where(
        EntityArtifactProvenanceModel.entity_id == saved.id,
        EntityArtifactProvenanceModel.artifact_id == artifact.id,
    )
    res = await db_session.execute(stmt)
    prov = res.scalar_one()

    assert prov.extraction_id == extraction_2
    assert prov.confidence == "HIGH"
    assert prov.evidence["evidence_snippet"] == "Updated extraction"
    assert prov.evidence["source_location"] == "loc 2"


# -----------------------------------------------------------------------------
# Test 15: Transaction rollback behavior if persistence fails
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transaction_rollback_behavior_if_persistence_fails(db_session: AsyncSession) -> None:
    """Verifies that if any part of persist_graph fails, the entire batch is rolled back leaving 0 partial records."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # Valid candidate entities
    candidate_valid_1 = GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Rust")
    candidate_valid_2 = GraphEntity(user_id=user.id, entity_type=EntityType.PROJECT, name="Kernel")

    # Invalid candidate relationship referencing a non-existent foreign key entity ID
    invalid_rel = GraphRelationship(
        user_id=user.id,
        source_entity_id=candidate_valid_2.id,
        target_entity_id=uuid4(),  # Entity doesn't exist anywhere
        relationship_type=RelationshipType.USES,
    )

    with pytest.raises(GraphEntityNotFoundError):
        await repo.persist_graph(
            entities=[candidate_valid_1, candidate_valid_2],
            relationships=[invalid_rel],
        )

    # Verify that neither candidate_valid_1 nor candidate_valid_2 was committed to DB
    stmt_entities = select(GraphEntityModel).where(
        GraphEntityModel.user_id == user.id,
        GraphEntityModel.canonical_name.in_(["rust", "kernel"]),
    )
    res = await db_session.execute(stmt_entities)
    persisted = res.scalars().all()
    assert len(persisted) == 0, "Partial entities must be rolled back on batch failure"


# -----------------------------------------------------------------------------
# Test 16: get_entity_by_id and get_entity_by_canonical
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_entity_by_id_and_canonical(db_session: AsyncSession) -> None:
    """Verifies reading entities by ID and by canonical key."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    entity = GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Amazon Web Services")
    saved = await repo.save_entity(entity)

    # By ID
    by_id = await repo.get_entity_by_id(saved.id)
    assert by_id is not None
    assert by_id.name == "Amazon Web Services"

    # Non-existent ID
    assert await repo.get_entity_by_id(uuid4()) is None

    # By Canonical
    by_canon = await repo.get_entity_by_canonical(user.id, EntityType.COMPANY, "amazon web services")
    assert by_canon is not None
    assert by_canon.id == saved.id

    # Non-existent Canonical
    assert await repo.get_entity_by_canonical(user.id, EntityType.COMPANY, "microsoft") is None


# -----------------------------------------------------------------------------
# Test 17: list_entities_by_user (with and without filter)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_entities_by_user(db_session: AsyncSession) -> None:
    """Verifies listing user entities, with and without entity_type filter."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Go"))
    await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="C++"))
    await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Uber"))

    # All entities for user
    all_user_entities = await repo.list_entities_by_user(user.id)
    assert len(all_user_entities) == 3

    # Filtered by SKILL
    skills = await repo.list_entities_by_user(user.id, entity_type=EntityType.SKILL)
    assert len(skills) == 2
    assert [s.name for s in skills] == ["C++", "Go"]  # Ordered by canonical_name ASC

    # Filtered by ROLE (none exist)
    roles = await repo.list_entities_by_user(user.id, entity_type=EntityType.ROLE)
    assert len(roles) == 0


# -----------------------------------------------------------------------------
# Test 18: get_relationship_by_id
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_relationship_by_id(db_session: AsyncSession) -> None:
    """Verifies reading relationship by primary key UUID."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    e1 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Dev"))
    e2 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Startup"))

    rel = await repo.save_relationship(
        GraphRelationship(
            user_id=user.id,
            source_entity_id=e1.id,
            target_entity_id=e2.id,
            relationship_type=RelationshipType.HELD_ROLE,
        )
    )

    found = await repo.get_relationship_by_id(rel.id)
    assert found is not None
    assert found.id == rel.id

    assert await repo.get_relationship_by_id(uuid4()) is None


# -----------------------------------------------------------------------------
# Test 19: get_user_graph (unfiltered, filtered by artifact_id, filtered by entity_type)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_user_graph_filtering(db_session: AsyncSession) -> None:
    """Verifies get_user_graph query behavior with artifact and entity_type filters."""
    user = await _create_test_user(db_session)
    artifact_1 = await _create_test_artifact(db_session, user.id)
    artifact_2 = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    prov_1 = GraphProvenance(artifact_id=artifact_1.id)
    prov_2 = GraphProvenance(artifact_id=artifact_2.id)

    skill = await repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="PyTorch"),
        provenance=prov_1,
    )
    proj = await repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.PROJECT, name="VisionNet"),
        provenance=prov_1,
    )
    company = await repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="OpenAI"),
        provenance=prov_2,
    )

    rel_1 = await repo.save_relationship(
        GraphRelationship(
            user_id=user.id,
            source_entity_id=proj.id,
            target_entity_id=skill.id,
            relationship_type=RelationshipType.USES,
        ),
        provenance=prov_1,
    )

    # 1. Unfiltered
    entities_all, rels_all = await repo.get_user_graph(user.id)
    assert len(entities_all) == 3
    assert len(rels_all) == 1

    # 2. Filtered by artifact_1
    entities_art1, rels_art1 = await repo.get_user_graph(user.id, artifact_id=artifact_1.id)
    assert len(entities_art1) == 2
    assert len(rels_art1) == 1

    # 3. Filtered by artifact_2
    entities_art2, rels_art2 = await repo.get_user_graph(user.id, artifact_id=artifact_2.id)
    assert len(entities_art2) == 1
    assert entities_art2[0].name == "OpenAI"
    assert len(rels_art2) == 0

    # 4. Filtered by entity_type SKILL
    entities_skill, rels_skill = await repo.get_user_graph(user.id, entity_type=EntityType.SKILL)
    assert len(entities_skill) == 1
    assert entities_skill[0].name == "PyTorch"


# -----------------------------------------------------------------------------
# Test 20: delete_entity
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_entity(db_session: AsyncSession) -> None:
    """Verifies deleting an entity removes it from the database."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    entity = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Kotlin"))

    deleted = await repo.delete_entity(entity.id)
    assert deleted is True

    # Subsequent fetch returns None
    assert await repo.get_entity_by_id(entity.id) is None

    # Deleting non-existent returns False
    assert await repo.delete_entity(uuid4()) is False


# -----------------------------------------------------------------------------
# Test 21: delete_provenance_by_artifact_id
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_provenance_by_artifact_id(db_session: AsyncSession) -> None:
    """Verifies deleting provenance records by artifact ID cleans up entity and relationship provenance."""
    user = await _create_test_user(db_session)
    artifact = await _create_test_artifact(db_session, user.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    prov = GraphProvenance(artifact_id=artifact.id)
    e1 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="QA"), provenance=prov)
    e2 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="QA Inc"), provenance=prov)
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=e1.id, target_entity_id=e2.id, relationship_type=RelationshipType.HELD_ROLE),
        provenance=prov,
    )

    deleted = await repo.delete_provenance_by_artifact_id(artifact.id)
    assert deleted is True

    # Entities and relationships still exist
    assert await repo.get_entity_by_id(e1.id) is not None
    assert await repo.get_entity_by_id(e2.id) is not None

    # But provenance is gone
    entities_art, rels_art = await repo.get_user_graph(user.id, artifact_id=artifact.id)
    assert len(entities_art) == 0
    assert len(rels_art) == 0

    # Second delete returns False
    assert await repo.delete_provenance_by_artifact_id(artifact.id) is False


# -----------------------------------------------------------------------------
# Test 22: get_provenance_for_entities (batch lookup and user isolation)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_provenance_for_entities_batch(db_session: AsyncSession) -> None:
    """Verifies batch retrieval of entity provenance records with multi-provenance and isolation."""
    user1 = await _create_test_user(db_session)
    user2 = await _create_test_user(db_session)
    art1 = await _create_test_artifact(db_session, user1.id)
    art2 = await _create_test_artifact(db_session, user1.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # Empty list returns empty dict
    assert await repo.get_provenance_for_entities(user1.id, []) == {}

    # Entity with multiple provenance citations
    e1 = await repo.save_entity(
        GraphEntity(user_id=user1.id, entity_type=EntityType.SKILL, name="Python"),
        provenance=GraphProvenance(artifact_id=art1.id, confidence="HIGH", evidence_snippet="5 yrs Python"),
    )
    # Re-save with second artifact provenance
    await repo.save_entity(
        GraphEntity(user_id=user1.id, entity_type=EntityType.SKILL, name="Python"),
        provenance=GraphProvenance(artifact_id=art2.id, confidence="MEDIUM", evidence_snippet="Python Certificate"),
    )

    # Entity without provenance
    e2 = await repo.save_entity(
        GraphEntity(user_id=user1.id, entity_type=EntityType.COMPANY, name="TechCorp")
    )

    prov_map = await repo.get_provenance_for_entities(user1.id, [e1.id, e2.id])
    assert len(prov_map[e1.id]) == 2
    assert {p.artifact_id for p in prov_map[e1.id]} == {art1.id, art2.id}
    assert prov_map[e2.id] == []

    # User 2 cannot access User 1's entity provenance
    prov_map_user2 = await repo.get_provenance_for_entities(user2.id, [e1.id])
    assert prov_map_user2[e1.id] == []


# -----------------------------------------------------------------------------
# Test 23: get_provenance_for_relationships (batch lookup and user isolation)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_provenance_for_relationships_batch(db_session: AsyncSession) -> None:
    """Verifies batch retrieval of relationship provenance records and isolation."""
    user1 = await _create_test_user(db_session)
    user2 = await _create_test_user(db_session)
    art = await _create_test_artifact(db_session, user1.id)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    assert await repo.get_provenance_for_relationships(user1.id, []) == {}

    e1 = await repo.save_entity(GraphEntity(user_id=user1.id, entity_type=EntityType.ROLE, name="Engineer"))
    e2 = await repo.save_entity(GraphEntity(user_id=user1.id, entity_type=EntityType.COMPANY, name="Global Corp"))

    prov = GraphProvenance(artifact_id=art.id, confidence="HIGH", evidence_snippet="Software Engineer at Global Corp")
    rel = await repo.save_relationship(
        GraphRelationship(
            user_id=user1.id,
            source_entity_id=e1.id,
            target_entity_id=e2.id,
            relationship_type=RelationshipType.WORKED_AT,
        ),
        provenance=prov,
    )

    prov_map = await repo.get_provenance_for_relationships(user1.id, [rel.id])
    assert len(prov_map[rel.id]) == 1
    assert prov_map[rel.id][0].artifact_id == art.id
    assert prov_map[rel.id][0].evidence_snippet == "Software Engineer at Global Corp"

    # User 2 cannot access User 1's relationship provenance
    prov_map_user2 = await repo.get_provenance_for_relationships(user2.id, [rel.id])
    assert prov_map_user2[rel.id] == []


"""Integration tests for experience_count aggregation in SQLAlchemyKnowledgeGraphRepository."""

from uuid import uuid4
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
from app.infrastructure.db.base import Base
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


async def _create_test_user(session: AsyncSession) -> UserModel:
    user = UserModel(
        id=uuid4(),
        email=f"exp_test_{uuid4().hex[:8]}@example.com",
        password_hash="hash",
        full_name="Experience Test User",
    )
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_experience_count_counts_role_nodes_only_not_company(db_session: AsyncSession) -> None:
    """Verifies that experience_count counts ONLY distinct ROLE nodes connected via USES,
    and never counts COMPANY nodes (change #1).
    """
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # 1. Create SKILL entity: Python
    python = await repo.save_entity(
        GraphEntity(user_id=user.id, entity_type=EntityType.SKILL, name="Python"),
        provenance=GraphProvenance(artifact_id=uuid4(), confidence="HIGH"),
    )

    # 2. Create 3 distinct ROLE entities
    role1 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Junior Dev"))
    role2 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Mid Dev"))
    role3 = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Senior Dev"))

    # 3. Create 1 COMPANY entity connected WORKED_AT to the roles
    company = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.COMPANY, name="Acme Corp"))
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role1.id, target_entity_id=company.id, relationship_type=RelationshipType.WORKED_AT)
    )
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role2.id, target_entity_id=company.id, relationship_type=RelationshipType.WORKED_AT)
    )

    # 4. Connect all 3 ROLE nodes to Python via USES
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role1.id, target_entity_id=python.id, relationship_type=RelationshipType.USES)
    )
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role2.id, target_entity_id=python.id, relationship_type=RelationshipType.USES)
    )
    await repo.save_relationship(
        GraphRelationship(user_id=user.id, source_entity_id=role3.id, target_entity_id=python.id, relationship_type=RelationshipType.USES)
    )

    # 5. Fetch skill metric profiles
    profiles = await repo.get_skill_metric_profiles(user.id)
    assert len(profiles) == 1
    py_profile = profiles[0]

    # experience_count must be 3 (the three ROLE nodes), NOT 1 (the single company) or 4
    assert py_profile.experience_count == 3
    assert py_profile.project_count == 0
    assert py_profile.certificate_count == 0

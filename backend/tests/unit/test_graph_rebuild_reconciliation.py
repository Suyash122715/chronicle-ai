"""Unit tests for graph rebuild, property reconciliation, and order-independence invariants."""

from datetime import datetime, timezone
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
        email=f"rebuild_test_{uuid4().hex[:8]}@example.com",
        password_hash="hash",
        full_name="Rebuild Test User",
    )
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_property_reconciliation_earliest_wins_on_collision(db_session: AsyncSession) -> None:
    """Verifies that when two artifacts contribute the same entity, the earlier property value
    is retained on key collision and new keys are added (change #9).
    """
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    # First artifact: sets "version": "1.0", "source": "artifact_1"
    e1 = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.TECHNOLOGY,
        name="Python",
        properties={"version": "1.0", "source": "artifact_1"},
    )
    saved_1 = await repo.save_entity(e1)
    assert saved_1.properties["version"] == "1.0"
    assert saved_1.properties["source"] == "artifact_1"

    # Second artifact: attempts to set "version": "2.0", and adds "ecosystem": "backend"
    e2 = GraphEntity(
        user_id=user.id,
        entity_type=EntityType.TECHNOLOGY,
        name="Python",
        properties={"version": "2.0", "ecosystem": "backend"},
    )
    saved_2 = await repo.save_entity(e2)
    assert saved_2.id == saved_1.id
    # Collision resolution: earlier value "1.0" is kept; "ecosystem" is merged in
    assert saved_2.properties["version"] == "1.0"
    assert saved_2.properties["source"] == "artifact_1"
    assert saved_2.properties["ecosystem"] == "backend"


@pytest.mark.asyncio
async def test_relationship_weight_max_evidence_wins(db_session: AsyncSession) -> None:
    """Verifies that relationship weight becomes the maximum of all contributing artifacts."""
    user = await _create_test_user(db_session)
    repo = SQLAlchemyKnowledgeGraphRepository(db_session)

    src = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.ROLE, name="Dev"))
    tgt = await repo.save_entity(GraphEntity(user_id=user.id, entity_type=EntityType.TECHNOLOGY, name="Go"))

    # Initial relationship with weight 0.5
    r1 = GraphRelationship(
        user_id=user.id,
        source_entity_id=src.id,
        target_entity_id=tgt.id,
        relationship_type=RelationshipType.USES,
        weight=0.5,
    )
    saved_r1 = await repo.save_relationship(r1)
    assert saved_r1.weight == 0.5

    # Second relationship with weight 0.9 -> weight should update to 0.9 (max)
    r2 = GraphRelationship(
        user_id=user.id,
        source_entity_id=src.id,
        target_entity_id=tgt.id,
        relationship_type=RelationshipType.USES,
        weight=0.9,
    )
    saved_r2 = await repo.save_relationship(r2)
    assert saved_r2.weight == 0.9

    # Third relationship with weight 0.3 -> weight stays 0.9
    r3 = GraphRelationship(
        user_id=user.id,
        source_entity_id=src.id,
        target_entity_id=tgt.id,
        relationship_type=RelationshipType.USES,
        weight=0.3,
    )
    saved_r3 = await repo.save_relationship(r3)
    assert saved_r3.weight == 0.9

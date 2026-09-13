"""Unit tests for GetKnowledgeGraphUseCase."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from app.application.knowledge_graph.get.get_knowledge_graph_use_case import (
    GetKnowledgeGraphUseCase,
    KnowledgeGraphQueryResult,
)
from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.exceptions.artifact_exceptions import ArtifactNotFoundError
from app.domain.exceptions.base import DomainValidationError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType


@pytest.fixture
def mock_kg_repository() -> MagicMock:
    return MagicMock(spec=KnowledgeGraphRepositoryInterface)


@pytest.fixture
def mock_artifact_repository() -> MagicMock:
    return MagicMock(spec=ArtifactRepositoryInterface)


@pytest.fixture
def use_case(
    mock_kg_repository: MagicMock, mock_artifact_repository: MagicMock
) -> GetKnowledgeGraphUseCase:
    return GetKnowledgeGraphUseCase(
        knowledge_graph_repository=mock_kg_repository,
        artifact_repository=mock_artifact_repository,
    )


@pytest.mark.asyncio
async def test_get_knowledge_graph_success_with_provenance(
    use_case: GetKnowledgeGraphUseCase,
    mock_kg_repository: MagicMock,
    mock_artifact_repository: MagicMock,
) -> None:
    """Verifies retrieval of full graph with batch provenance lookups."""
    user_id = uuid4()
    entity1 = GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Python")
    entity2 = GraphEntity(user_id=user_id, entity_type=EntityType.COMPANY, name="Acme Corp")
    rel = GraphRelationship(
        user_id=user_id,
        source_entity_id=entity1.id,
        target_entity_id=entity2.id,
        relationship_type=RelationshipType.RELATED_TO,
    )

    prov_entity = GraphProvenance(artifact_id=uuid4(), confidence="HIGH", evidence_snippet="Proficient in Python")
    prov_rel = GraphProvenance(artifact_id=uuid4(), confidence="MEDIUM")

    mock_kg_repository.get_user_graph = AsyncMock(return_value=([entity1, entity2], [rel]))
    mock_kg_repository.get_provenance_for_entities = AsyncMock(
        return_value={entity1.id: [prov_entity], entity2.id: []}
    )
    mock_kg_repository.get_provenance_for_relationships = AsyncMock(
        return_value={rel.id: [prov_rel]}
    )

    result = await use_case.execute(user_id=user_id, include_provenance=True)

    assert isinstance(result, KnowledgeGraphQueryResult)
    assert len(result.entities) == 2
    assert len(result.relationships) == 1
    assert result.entity_provenance[entity1.id] == [prov_entity]
    assert result.relationship_provenance[rel.id] == [prov_rel]

    mock_kg_repository.get_user_graph.assert_awaited_once_with(
        user_id=user_id,
        artifact_id=None,
        entity_type=None,
    )
    mock_kg_repository.get_provenance_for_entities.assert_awaited_once_with(
        user_id=user_id,
        entity_ids=[entity1.id, entity2.id],
    )
    mock_kg_repository.get_provenance_for_relationships.assert_awaited_once_with(
        user_id=user_id,
        relationship_ids=[rel.id],
    )


@pytest.mark.asyncio
async def test_get_knowledge_graph_success_without_provenance(
    use_case: GetKnowledgeGraphUseCase,
    mock_kg_repository: MagicMock,
) -> None:
    """Verifies that include_provenance=False bypasses provenance queries entirely."""
    user_id = uuid4()
    entity = GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Go")
    mock_kg_repository.get_user_graph = AsyncMock(return_value=([entity], []))
    mock_kg_repository.get_provenance_for_entities = AsyncMock()
    mock_kg_repository.get_provenance_for_relationships = AsyncMock()

    result = await use_case.execute(user_id=user_id, include_provenance=False)

    assert len(result.entities) == 1
    assert len(result.relationships) == 0
    assert result.entity_provenance == {}
    assert result.relationship_provenance == {}

    mock_kg_repository.get_provenance_for_entities.assert_not_called()
    mock_kg_repository.get_provenance_for_relationships.assert_not_called()


@pytest.mark.asyncio
async def test_get_knowledge_graph_filters_by_entity_type(
    use_case: GetKnowledgeGraphUseCase,
    mock_kg_repository: MagicMock,
) -> None:
    """Verifies entity_type filter is properly parsed and forwarded to repository."""
    user_id = uuid4()
    mock_kg_repository.get_user_graph = AsyncMock(return_value=([], []))

    result = await use_case.execute(user_id=user_id, entity_type="skill", include_provenance=False)

    assert len(result.entities) == 0
    mock_kg_repository.get_user_graph.assert_awaited_once_with(
        user_id=user_id,
        artifact_id=None,
        entity_type=EntityType.SKILL,
    )


@pytest.mark.asyncio
async def test_get_knowledge_graph_invalid_entity_type_raises_validation_error(
    use_case: GetKnowledgeGraphUseCase,
) -> None:
    """Verifies invalid entity_type string raises DomainValidationError."""
    user_id = uuid4()

    with pytest.raises(DomainValidationError) as exc_info:
        await use_case.execute(user_id=user_id, entity_type="INVALID_TYPE")

    assert "Invalid entity_type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_knowledge_graph_filters_by_artifact_id_success(
    use_case: GetKnowledgeGraphUseCase,
    mock_kg_repository: MagicMock,
    mock_artifact_repository: MagicMock,
) -> None:
    """Verifies artifact ownership check succeeds for matching user_id."""
    user_id = uuid4()
    artifact_id = uuid4()
    artifact = Artifact(
        id=artifact_id,
        user_id=user_id,
        filename="resume.pdf",
        stored_filename="stored.pdf",
        file_path="/tmp/stored.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.COMPLETED,
    )
    mock_artifact_repository.get_by_id = AsyncMock(return_value=artifact)
    mock_kg_repository.get_user_graph = AsyncMock(return_value=([], []))

    result = await use_case.execute(
        user_id=user_id, artifact_id=artifact_id, include_provenance=False
    )

    assert len(result.entities) == 0
    mock_artifact_repository.get_by_id.assert_awaited_once_with(artifact_id)
    mock_kg_repository.get_user_graph.assert_awaited_once_with(
        user_id=user_id,
        artifact_id=artifact_id,
        entity_type=None,
    )


@pytest.mark.asyncio
async def test_get_knowledge_graph_cross_user_artifact_raises_404(
    use_case: GetKnowledgeGraphUseCase,
    mock_artifact_repository: MagicMock,
) -> None:
    """Verifies that requesting an artifact owned by another user raises ArtifactNotFoundError."""
    user_id = uuid4()
    other_user_id = uuid4()
    artifact_id = uuid4()
    artifact = Artifact(
        id=artifact_id,
        user_id=other_user_id,  # Different user!
        filename="other.pdf",
        stored_filename="other.pdf",
        file_path="/tmp/other.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.COMPLETED,
    )
    mock_artifact_repository.get_by_id = AsyncMock(return_value=artifact)

    with pytest.raises(ArtifactNotFoundError):
        await use_case.execute(user_id=user_id, artifact_id=artifact_id)


@pytest.mark.asyncio
async def test_get_knowledge_graph_nonexistent_artifact_raises_404(
    use_case: GetKnowledgeGraphUseCase,
    mock_artifact_repository: MagicMock,
) -> None:
    """Verifies that requesting a non-existent artifact raises ArtifactNotFoundError."""
    user_id = uuid4()
    mock_artifact_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ArtifactNotFoundError):
        await use_case.execute(user_id=user_id, artifact_id=uuid4())


@pytest.mark.asyncio
async def test_get_knowledge_graph_empty_graph_returns_empty_result(
    use_case: GetKnowledgeGraphUseCase,
    mock_kg_repository: MagicMock,
) -> None:
    """Verifies that empty graph returns cleanly with zero counts and empty collections."""
    user_id = uuid4()
    mock_kg_repository.get_user_graph = AsyncMock(return_value=([], []))
    mock_kg_repository.get_provenance_for_entities = AsyncMock()
    mock_kg_repository.get_provenance_for_relationships = AsyncMock()

    result = await use_case.execute(user_id=user_id, include_provenance=True)

    assert result.entities == []
    assert result.relationships == []
    assert result.entity_provenance == {}
    assert result.relationship_provenance == {}
    # When entities/relationships are empty, batch provenance lookup should not be called
    mock_kg_repository.get_provenance_for_entities.assert_not_called()
    mock_kg_repository.get_provenance_for_relationships.assert_not_called()

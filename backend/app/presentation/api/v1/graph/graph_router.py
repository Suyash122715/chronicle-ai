"""Knowledge Graph router exposing read endpoints for querying graphs."""

from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.application.knowledge_graph.get.get_knowledge_graph_use_case import GetKnowledgeGraphUseCase
from app.dependencies import get_current_user, get_get_knowledge_graph_use_case
from app.domain.entities.user import User
from app.presentation.schemas.graph_response import KnowledgeGraphResponse

graph_router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@graph_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=KnowledgeGraphResponse,
    summary="Get User Knowledge Graph",
    description="Retrieves the authenticated user's knowledge graph of entities and relationships with optional filters.",
)
async def get_user_knowledge_graph(
    artifact_id: UUID | None = Query(
        None,
        description="Filter graph to nodes and edges originating from a specific artifact.",
    ),
    entity_type: str | None = Query(
        None,
        description="Filter nodes by EntityType (e.g. SKILL, PROJECT, COMPANY, ROLE, TECHNOLOGY, CERTIFICATE, INSTITUTION, ACHIEVEMENT).",
    ),
    include_provenance: bool = Query(
        True,
        description="Whether to include origin artifact citations, confidence levels, and evidence snippets.",
    ),
    current_user: User = Depends(get_current_user),
    use_case: GetKnowledgeGraphUseCase = Depends(get_get_knowledge_graph_use_case),
) -> KnowledgeGraphResponse:
    """Handles GET /api/v1/graph."""
    result = await use_case.execute(
        user_id=current_user.id,
        artifact_id=artifact_id,
        entity_type=entity_type,
        include_provenance=include_provenance,
    )
    return KnowledgeGraphResponse.from_query_result(result)

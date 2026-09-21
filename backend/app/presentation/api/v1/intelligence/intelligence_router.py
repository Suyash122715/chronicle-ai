"""Career Intelligence router exposing read endpoints for skill intelligence and insights."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.career_intelligence.get_career_insights_use_case import GetCareerInsightsUseCase
from app.application.career_intelligence.get_skill_intelligence_use_case import (
    GetSkillIntelligenceUseCase,
)
from app.dependencies import (
    get_career_insights_use_case,
    get_current_user,
    get_skill_intelligence_use_case,
)
from app.domain.entities.user import User
from app.presentation.schemas.intelligence_response import (
    CareerInsightsResponse,
    SkillScoreListResponse,
    SkillScoreResponse,
)

intelligence_router = APIRouter(prefix="/intelligence", tags=["Career Intelligence"])


@intelligence_router.get(
    "/skills",
    status_code=status.HTTP_200_OK,
    response_model=SkillScoreListResponse,
    summary="Get Scored Skills & Technologies",
    description="Retrieves deterministic proficiency scores and metrics for all user skills and technologies.",
)
async def get_scored_skills(
    current_user: User = Depends(get_current_user),
    use_case: GetSkillIntelligenceUseCase = Depends(get_skill_intelligence_use_case),
) -> SkillScoreListResponse:
    """Handles GET /api/v1/intelligence/skills."""
    scores = await use_case.execute(user_id=current_user.id)
    items = [SkillScoreResponse.from_domain(s) for s in scores]
    return SkillScoreListResponse(items=items, total=len(items))


@intelligence_router.get(
    "/skills/{entity_id}",
    status_code=status.HTTP_200_OK,
    response_model=SkillScoreResponse,
    summary="Get Scored Skill By Entity ID",
    description="Retrieves deterministic proficiency score and metrics for a specific skill or technology entity.",
)
async def get_scored_skill_by_id(
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetSkillIntelligenceUseCase = Depends(get_skill_intelligence_use_case),
) -> SkillScoreResponse:
    """Handles GET /api/v1/intelligence/skills/{entity_id}."""
    score = await use_case.get_by_entity_id(user_id=current_user.id, entity_id=entity_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill or technology with entity ID '{entity_id}' not found.",
        )
    return SkillScoreResponse.from_domain(score)


@intelligence_router.get(
    "/summary",
    status_code=status.HTTP_200_OK,
    response_model=CareerInsightsResponse,
    summary="Get Career Intelligence Summary",
    description="Retrieves aggregate strengths, top competencies, and evidence metrics.",
)
async def get_career_summary(
    top_n: int = Query(5, ge=1, le=50, description="Number of top skills to include."),
    current_user: User = Depends(get_current_user),
    use_case: GetCareerInsightsUseCase = Depends(get_career_insights_use_case),
) -> CareerInsightsResponse:
    """Handles GET /api/v1/intelligence/summary."""
    insights = await use_case.execute(user_id=current_user.id, top_n=top_n)
    return CareerInsightsResponse.from_domain(insights)

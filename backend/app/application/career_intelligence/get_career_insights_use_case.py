"""GetCareerInsightsUseCase — computes high-level career insights and summary statistics."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.career_intelligence.get_skill_intelligence_use_case import GetSkillIntelligenceUseCase
from app.domain.career_intelligence.proficiency_level import ProficiencyLevel
from app.domain.career_intelligence.skill_score import SkillScore
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface


@dataclass(frozen=True)
class CareerInsights:
    """Summary metrics and top strengths for a user's career profile."""

    total_competencies: int
    top_skills: list[SkillScore]
    evidence_light_count: int
    evidence_light_skills: list[SkillScore]
    expert_count: int
    advanced_count: int
    intermediate_count: int
    beginner_count: int


class GetCareerInsightsUseCase:
    """Computes high-level career intelligence summary and top competencies."""

    def __init__(
        self,
        kg_repo: KnowledgeGraphRepositoryInterface,
        skill_intelligence_use_case: GetSkillIntelligenceUseCase | None = None,
    ) -> None:
        self._kg_repo = kg_repo
        self._skill_intelligence_use_case = (
            skill_intelligence_use_case or GetSkillIntelligenceUseCase(kg_repo=kg_repo)
        )

    async def execute(self, user_id: UUID, top_n: int = 5) -> CareerInsights:
        """Assembles career insights for the given user.

        Args:
            user_id: UUID of the user.
            top_n: Number of top skills to include in top_skills.

        Returns:
            CareerInsights value object.
        """
        all_skills = await self._skill_intelligence_use_case.execute(user_id)

        evidence_light_skills = [s for s in all_skills if s.evidence_light]
        top_skills = all_skills[:top_n]

        expert_count = sum(1 for s in all_skills if s.proficiency_level == ProficiencyLevel.EXPERT)
        advanced_count = sum(1 for s in all_skills if s.proficiency_level == ProficiencyLevel.ADVANCED)
        intermediate_count = sum(1 for s in all_skills if s.proficiency_level == ProficiencyLevel.INTERMEDIATE)
        beginner_count = sum(1 for s in all_skills if s.proficiency_level == ProficiencyLevel.BEGINNER)

        return CareerInsights(
            total_competencies=len(all_skills),
            top_skills=top_skills,
            evidence_light_count=len(evidence_light_skills),
            evidence_light_skills=evidence_light_skills,
            expert_count=expert_count,
            advanced_count=advanced_count,
            intermediate_count=intermediate_count,
            beginner_count=beginner_count,
        )

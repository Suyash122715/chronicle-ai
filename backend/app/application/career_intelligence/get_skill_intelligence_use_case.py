"""GetSkillIntelligenceUseCase — retrieves, associates, and scores all skills/technologies for a user."""

from __future__ import annotations

from uuid import UUID

from app.domain.career_intelligence.deterministic_skill_scorer import DeterministicSkillScorer
from app.domain.career_intelligence.skill_score import SkillScore
from app.domain.career_intelligence.skill_technology_associator import SkillTechnologyAssociator
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface


class GetSkillIntelligenceUseCase:
    """Retrieves raw metric profiles from the Knowledge Graph, groups logically equivalent
    SKILL and TECHNOLOGY entities, scores each competency deterministically, and returns
    a sorted list of SkillScore objects.
    """

    def __init__(
        self,
        kg_repo: KnowledgeGraphRepositoryInterface,
        scorer: DeterministicSkillScorer | None = None,
        associator: SkillTechnologyAssociator | None = None,
    ) -> None:
        self._kg_repo = kg_repo
        self._scorer = scorer or DeterministicSkillScorer()
        self._associator = associator or SkillTechnologyAssociator()

    async def execute(self, user_id: UUID) -> list[SkillScore]:
        """Fetches metric profiles, associates equivalent SKILL/TECH nodes, and scores each competency.

        Returns:
            List of SkillScore objects, sorted by score descending, then canonical_name ascending.
        """
        profiles = await self._kg_repo.get_skill_metric_profiles(user_id)
        if not profiles:
            return []

        associations = self._associator.associate(profiles)
        scores = [self._scorer.score_association(assoc) for assoc in associations]

        # Deterministic sort: highest score first; tie-break alphabetically by canonical_name
        scores.sort(key=lambda s: (-s.score, s.canonical_name))
        return scores

    async def get_by_entity_id(self, user_id: UUID, entity_id: UUID) -> SkillScore | None:
        """Finds and returns a specific scored competency by either primary entity_id or tech_entity_id."""
        all_scores = await self.execute(user_id)
        for s in all_scores:
            if s.entity_id == entity_id or s.tech_entity_id == entity_id:
                return s
        return None

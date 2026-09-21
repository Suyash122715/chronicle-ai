"""DeterministicSkillScorer — applies the V1 scoring formula using fixed global constants.

Zero LLM calls. Zero randomness. Every invocation with the same input produces the same output.
"""

from __future__ import annotations

from app.domain.career_intelligence.career_intelligence_constants import (
    K_C,
    K_E,
    K_F,
    K_P,
    W_C,
    W_E,
    W_F,
    W_P,
)
from app.domain.career_intelligence.proficiency_level import ProficiencyLevel
from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.career_intelligence.skill_score import SkillScore
from app.domain.career_intelligence.skill_technology_association import SkillTechnologyAssociation
from app.domain.value_objects.entity_type import EntityType


class DeterministicSkillScorer:
    """Applies the V1 Career Intelligence scoring formula to produce SkillScore objects.

    Formula (from career_intelligence_constants.py):
        Score(0..100) = 100 × (
            W_F × min(1.0, frequency        / K_F) +
            W_P × min(1.0, project_count    / K_P) +
            W_E × min(1.0, experience_count / K_E) +
            W_C × min(1.0, certificate_count / K_C)
        )

    All constants (W_*, K_*) are module-level literals imported from career_intelligence_constants.
    No runtime configuration, no LLM, no randomness.
    """

    @staticmethod
    def _compute_raw_score(
        frequency: int,
        project_count: int,
        experience_count: int,
        certificate_count: int,
    ) -> float:
        """Computes the raw score in [0.0, 100.0].

        Args:
            frequency: Distinct artifact count.
            project_count: Distinct PROJECT node count via USES.
            experience_count: Distinct ROLE node count via USES (COMPANY excluded).
            certificate_count: Distinct CERTIFICATE node count via CERTIFIED_IN.

        Returns:
            Float in [0.0, 100.0], rounded to 2 decimal places.
        """
        f_component = W_F * min(1.0, frequency / K_F)
        p_component = W_P * min(1.0, project_count / K_P)
        e_component = W_E * min(1.0, experience_count / K_E)
        c_component = W_C * min(1.0, certificate_count / K_C)
        raw = (f_component + p_component + e_component + c_component) * 100.0
        return round(min(100.0, max(0.0, raw)), 2)

    def score_profile(self, profile: SkillMetricProfile) -> SkillScore:
        """Scores a single SkillMetricProfile and returns a SkillScore.

        Args:
            profile: SkillMetricProfile for a SKILL or TECHNOLOGY entity.

        Returns:
            SkillScore with deterministic score and proficiency_level.
        """
        score = self._compute_raw_score(
            frequency=profile.frequency,
            project_count=profile.project_count,
            experience_count=profile.experience_count,
            certificate_count=profile.certificate_count,
        )
        return SkillScore(
            entity_id=profile.entity_id,
            tech_entity_id=None,
            canonical_name=profile.canonical_name,
            entity_type=profile.entity_type,
            score=score,
            proficiency_level=ProficiencyLevel.from_score(score),
            frequency=profile.frequency,
            project_count=profile.project_count,
            experience_count=profile.experience_count,
            certificate_count=profile.certificate_count,
            evidence_light=profile.evidence_light,
        )

    def score_association(self, association: SkillTechnologyAssociation) -> SkillScore:
        """Scores a SkillTechnologyAssociation (aggregated competency) and returns a SkillScore.

        When both SKILL and TECHNOLOGY entities exist, the primary entity_id is the SKILL's ID.
        The tech_entity_id carries the TECHNOLOGY entity's ID for consumer traceability.

        Args:
            association: SkillTechnologyAssociation grouping one or both entity types.

        Returns:
            SkillScore with both entity IDs present when applicable.
        """
        score = self._compute_raw_score(
            frequency=association.frequency,
            project_count=association.project_count,
            experience_count=association.experience_count,
            certificate_count=association.certificate_count,
        )

        # Primary entity_id: prefer SKILL; fall back to TECHNOLOGY
        primary_id = (
            association.skill_entity_id
            if association.skill_entity_id is not None
            else association.tech_entity_id
        )
        assert primary_id is not None, "SkillTechnologyAssociation must have at least one entity ID"

        # entity_type of the primary entity
        primary_type = (
            EntityType.SKILL
            if association.skill_entity_id is not None
            else EntityType.TECHNOLOGY
        )

        return SkillScore(
            entity_id=primary_id,
            tech_entity_id=association.tech_entity_id
            if association.skill_entity_id is not None
            else None,
            canonical_name=association.competency_name,
            entity_type=primary_type,
            score=score,
            proficiency_level=ProficiencyLevel.from_score(score),
            frequency=association.frequency,
            project_count=association.project_count,
            experience_count=association.experience_count,
            certificate_count=association.certificate_count,
            evidence_light=association.evidence_light,
        )

"""Unit tests for DeterministicSkillScorer and scoring formula invariants."""

import pytest
from uuid import uuid4

from app.domain.career_intelligence.deterministic_skill_scorer import DeterministicSkillScorer
from app.domain.career_intelligence.proficiency_level import ProficiencyLevel
from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.career_intelligence.skill_technology_association import SkillTechnologyAssociation
from app.domain.value_objects.entity_type import EntityType


def test_experience_count_only_role_nodes() -> None:
    """Verifies that experience_count reflects distinct ROLE nodes via USES (change #1).
    Score calculation uses W_E=0.35, K_E=3.
    """
    scorer = DeterministicSkillScorer()
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="python",
        entity_type=EntityType.SKILL,
        frequency=1,
        project_count=0,
        experience_count=1,
        certificate_count=0,
    )
    # Score = 100 * (0.15 * (1/5) + 0.30 * 0 + 0.35 * (1/3) + 0.20 * 0)
    # = 100 * (0.03 + 0.116666...) = 14.67
    score = scorer.score_profile(profile)
    assert score.experience_count == 1
    assert score.score == 14.67
    assert score.proficiency_level == ProficiencyLevel.BEGINNER


def test_experience_saturation_at_k_e_threshold() -> None:
    """Verifies that 3 ROLE nodes saturate the experience component to 1.0 (K_E=3)."""
    scorer = DeterministicSkillScorer()
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="python",
        entity_type=EntityType.SKILL,
        frequency=0,
        project_count=0,
        experience_count=3,
        certificate_count=0,
    )
    # Score = 100 * (0.35 * min(1.0, 3/3)) = 35.00
    score = scorer.score_profile(profile)
    assert score.score == 35.00
    assert score.proficiency_level == ProficiencyLevel.INTERMEDIATE


def test_max_saturation_all_metrics() -> None:
    """Verifies all components at or above saturation yield exactly 100.0."""
    scorer = DeterministicSkillScorer()
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="python",
        entity_type=EntityType.SKILL,
        frequency=10,  # > K_F (5)
        project_count=8,  # > K_P (4)
        experience_count=6,  # > K_E (3)
        certificate_count=4,  # > K_C (2)
    )
    score = scorer.score_profile(profile)
    assert score.score == 100.0
    assert score.proficiency_level == ProficiencyLevel.EXPERT


def test_scorer_determinism_and_reproducibility() -> None:
    """Verifies scorer produces identical output for repeated calls with same input."""
    scorer = DeterministicSkillScorer()
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="react",
        entity_type=EntityType.TECHNOLOGY,
        frequency=3,
        project_count=2,
        experience_count=1,
        certificate_count=1,
    )
    s1 = scorer.score_profile(profile)
    s2 = scorer.score_profile(profile)
    assert s1.score == s2.score
    assert s1.proficiency_level == s2.proficiency_level


def test_proficiency_level_boundaries() -> None:
    """Verifies proficiency level tier assignments at exact boundaries."""
    assert ProficiencyLevel.from_score(0.0) == ProficiencyLevel.BEGINNER
    assert ProficiencyLevel.from_score(24.99) == ProficiencyLevel.BEGINNER
    assert ProficiencyLevel.from_score(25.0) == ProficiencyLevel.INTERMEDIATE
    assert ProficiencyLevel.from_score(54.99) == ProficiencyLevel.INTERMEDIATE
    assert ProficiencyLevel.from_score(55.0) == ProficiencyLevel.ADVANCED
    assert ProficiencyLevel.from_score(79.99) == ProficiencyLevel.ADVANCED
    assert ProficiencyLevel.from_score(80.0) == ProficiencyLevel.EXPERT
    assert ProficiencyLevel.from_score(100.0) == ProficiencyLevel.EXPERT


def test_score_association_preserves_both_ids() -> None:
    """Verifies scoring an association retains both skill_entity_id and tech_entity_id."""
    scorer = DeterministicSkillScorer()
    skill_id = uuid4()
    tech_id = uuid4()
    assoc = SkillTechnologyAssociation(
        competency_name="python",
        skill_entity_id=skill_id,
        tech_entity_id=tech_id,
        frequency=4,
        project_count=2,
        experience_count=2,
        certificate_count=1,
    )
    score = scorer.score_association(assoc)
    assert score.entity_id == skill_id
    assert score.tech_entity_id == tech_id
    assert score.canonical_name == "python"
    assert score.entity_type == EntityType.SKILL

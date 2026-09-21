"""Unit tests for evidence_light boolean definition on profiles and associations."""

from uuid import uuid4

from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.career_intelligence.skill_technology_association import SkillTechnologyAssociation
from app.domain.value_objects.entity_type import EntityType


def test_profile_with_mentions_and_zero_applied_evidence_is_evidence_light() -> None:
    """Verifies frequency >= 1 with 0 projects, 0 experience, 0 certificates is evidence_light=True."""
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="haskell",
        entity_type=EntityType.SKILL,
        frequency=2,
        project_count=0,
        experience_count=0,
        certificate_count=0,
    )
    assert profile.evidence_light is True


def test_profile_with_project_evidence_is_not_evidence_light() -> None:
    """Verifies profile with project_count > 0 is evidence_light=False."""
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="python",
        entity_type=EntityType.SKILL,
        frequency=1,
        project_count=1,
        experience_count=0,
        certificate_count=0,
    )
    assert profile.evidence_light is False


def test_profile_with_experience_evidence_is_not_evidence_light() -> None:
    """Verifies profile with experience_count > 0 is evidence_light=False."""
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="fastapi",
        entity_type=EntityType.TECHNOLOGY,
        frequency=1,
        project_count=0,
        experience_count=1,
        certificate_count=0,
    )
    assert profile.evidence_light is False


def test_profile_with_certificate_evidence_is_not_evidence_light() -> None:
    """Verifies profile with certificate_count > 0 is evidence_light=False."""
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="aws",
        entity_type=EntityType.TECHNOLOGY,
        frequency=1,
        project_count=0,
        experience_count=0,
        certificate_count=1,
    )
    assert profile.evidence_light is False


def test_profile_with_zero_frequency_is_not_evidence_light() -> None:
    """Verifies profile with frequency = 0 is evidence_light=False."""
    profile = SkillMetricProfile(
        entity_id=uuid4(),
        canonical_name="rust",
        entity_type=EntityType.SKILL,
        frequency=0,
        project_count=0,
        experience_count=0,
        certificate_count=0,
    )
    assert profile.evidence_light is False


def test_association_evidence_light_property() -> None:
    """Verifies evidence_light property on SkillTechnologyAssociation."""
    assoc_light = SkillTechnologyAssociation(
        competency_name="c++",
        skill_entity_id=uuid4(),
        tech_entity_id=None,
        frequency=1,
        project_count=0,
        experience_count=0,
        certificate_count=0,
    )
    assert assoc_light.evidence_light is True

    assoc_applied = SkillTechnologyAssociation(
        competency_name="c++",
        skill_entity_id=uuid4(),
        tech_entity_id=None,
        frequency=1,
        project_count=1,
        experience_count=0,
        certificate_count=0,
    )
    assert assoc_applied.evidence_light is False

"""Unit tests for SkillTechnologyAssociator domain service."""

from uuid import uuid4

from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.career_intelligence.skill_technology_associator import SkillTechnologyAssociator
from app.domain.value_objects.entity_type import EntityType


def test_associator_pairs_skill_and_technology_by_canonical_name() -> None:
    """Verifies that SKILL and TECHNOLOGY with same canonical_name produce one association
    with both entity IDs preserved and aggregated metrics (change #5).
    """
    skill_id = uuid4()
    tech_id = uuid4()
    profiles = [
        SkillMetricProfile(
            entity_id=skill_id,
            canonical_name="python",
            entity_type=EntityType.SKILL,
            frequency=2,
            project_count=1,
            experience_count=2,
            certificate_count=1,
        ),
        SkillMetricProfile(
            entity_id=tech_id,
            canonical_name="python",
            entity_type=EntityType.TECHNOLOGY,
            frequency=3,
            project_count=2,
            experience_count=1,
            certificate_count=0,
        ),
    ]

    associator = SkillTechnologyAssociator()
    associations = associator.associate(profiles)

    assert len(associations) == 1
    assoc = associations[0]
    assert assoc.competency_name == "python"
    assert assoc.skill_entity_id == skill_id
    assert assoc.tech_entity_id == tech_id
    # frequency uses max to prevent double counting: max(2, 3) = 3
    assert assoc.frequency == 3
    # applied metrics use max() to prevent double counting overlapping entities: max(1, 2) = 2, max(2, 1) = 2, max(1, 0) = 1
    assert assoc.project_count == 2
    assert assoc.experience_count == 2
    assert assoc.certificate_count == 1
    assert assoc.evidence_light is False


def test_single_skill_produces_association_with_none_tech_id() -> None:
    """Verifies a SKILL with no matching TECHNOLOGY produces an association with tech_entity_id=None."""
    skill_id = uuid4()
    profiles = [
        SkillMetricProfile(
            entity_id=skill_id,
            canonical_name="leadership",
            entity_type=EntityType.SKILL,
            frequency=2,
            project_count=0,
            experience_count=2,
            certificate_count=0,
        )
    ]

    associator = SkillTechnologyAssociator()
    associations = associator.associate(profiles)

    assert len(associations) == 1
    assoc = associations[0]
    assert assoc.competency_name == "leadership"
    assert assoc.skill_entity_id == skill_id
    assert assoc.tech_entity_id is None
    assert assoc.experience_count == 2


def test_single_technology_produces_association_with_none_skill_id() -> None:
    """Verifies a TECHNOLOGY with no matching SKILL produces an association with skill_entity_id=None."""
    tech_id = uuid4()
    profiles = [
        SkillMetricProfile(
            entity_id=tech_id,
            canonical_name="docker",
            entity_type=EntityType.TECHNOLOGY,
            frequency=3,
            project_count=4,
            experience_count=1,
            certificate_count=0,
        )
    ]

    associator = SkillTechnologyAssociator()
    associations = associator.associate(profiles)

    assert len(associations) == 1
    assoc = associations[0]
    assert assoc.competency_name == "docker"
    assert assoc.skill_entity_id is None
    assert assoc.tech_entity_id == tech_id
    assert assoc.project_count == 4


def test_associator_empty_input_returns_empty_list() -> None:
    """Verifies empty input yields empty list."""
    associator = SkillTechnologyAssociator()
    assert associator.associate([]) == []

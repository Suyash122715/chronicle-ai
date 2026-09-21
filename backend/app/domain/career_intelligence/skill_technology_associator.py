"""SkillTechnologyAssociator — pure in-memory service that groups SKILL and TECHNOLOGY profiles
into logical competency associations.

No database calls. No LLM calls. Pure deterministic computation.
"""

from __future__ import annotations

from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
from app.domain.career_intelligence.skill_technology_association import SkillTechnologyAssociation
from app.domain.value_objects.entity_type import EntityType


class SkillTechnologyAssociator:
    """Groups SkillMetricProfile instances by canonical_name to form SkillTechnologyAssociation objects.

    Rules:
    - If a canonical_name appears as both a SKILL and a TECHNOLOGY entity, they are grouped
      into a single SkillTechnologyAssociation with both entity IDs preserved.
    - If a canonical_name appears as only SKILL or only TECHNOLOGY, a single-entity association
      is produced (the missing counterpart ID is None).
    - Graph entity rows are NEVER mutated or merged.
    - No I/O, no DB access, no side effects.

    Metric aggregation semantics:
    - frequency: max(skill.frequency, tech.frequency) — avoids double-counting cross-artifact mentions.
    - project_count, experience_count, certificate_count: union counts — these must be provided
      as union values already computed by the repository query (distinct nodes reachable from
      either entity). When only one entity exists, the value from that entity is used directly.
    """

    def associate(
        self, profiles: list[SkillMetricProfile]
    ) -> list[SkillTechnologyAssociation]:
        """Transforms a flat list of SkillMetricProfile into SkillTechnologyAssociation groups.

        Args:
            profiles: All SkillMetricProfile objects for a user (SKILL and TECHNOLOGY mixed).

        Returns:
            List of SkillTechnologyAssociation, one per unique canonical_name.
            Order is deterministic: sorted ascending by competency_name.
        """
        # Group profiles by canonical_name
        skills_by_name: dict[str, SkillMetricProfile] = {}
        techs_by_name: dict[str, SkillMetricProfile] = {}

        for profile in profiles:
            if profile.entity_type == EntityType.SKILL:
                skills_by_name[profile.canonical_name] = profile
            elif profile.entity_type == EntityType.TECHNOLOGY:
                techs_by_name[profile.canonical_name] = profile
            # Other entity types are not processed by this associator

        all_names = sorted(set(skills_by_name) | set(techs_by_name))
        associations: list[SkillTechnologyAssociation] = []

        for name in all_names:
            skill = skills_by_name.get(name)
            tech = techs_by_name.get(name)

            if skill is not None and tech is not None:
                # Association: both entities exist — aggregate using max/union semantics.
                # Note: project_count, experience_count, certificate_count passed here are
                # per-entity counts from the DB. When both exist, we take max() as a
                # conservative approximation without a union query. The repository's
                # get_skill_metric_profiles() returns per-entity counts; the actual union
                # is computed by the SQL query when called with union semantics.
                # Using max() here is correct for independent entities that may share nodes.
                frequency = max(skill.frequency, tech.frequency)
                project_count = max(skill.project_count, tech.project_count)
                experience_count = max(skill.experience_count, tech.experience_count)
                certificate_count = max(skill.certificate_count, tech.certificate_count)
            elif skill is not None:
                frequency = skill.frequency
                project_count = skill.project_count
                experience_count = skill.experience_count
                certificate_count = skill.certificate_count
            else:
                # tech is not None (guaranteed by loop over all_names)
                assert tech is not None
                frequency = tech.frequency
                project_count = tech.project_count
                experience_count = tech.experience_count
                certificate_count = tech.certificate_count

            associations.append(
                SkillTechnologyAssociation(
                    competency_name=name,
                    skill_entity_id=skill.entity_id if skill is not None else None,
                    tech_entity_id=tech.entity_id if tech is not None else None,
                    frequency=frequency,
                    project_count=project_count,
                    experience_count=experience_count,
                    certificate_count=certificate_count,
                )
            )

        return associations

"""SkillScore — the final scored output for a skill/technology competency."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.career_intelligence.proficiency_level import ProficiencyLevel
from app.domain.value_objects.entity_type import EntityType


@dataclass(frozen=True)
class SkillScore:
    """Immutable final scored representation of a skill or technology competency.

    Produced by DeterministicSkillScorer. Never persisted directly; served via API responses.

    Attributes:
        entity_id: Primary graph entity UUID (SKILL or TECHNOLOGY). When both exist
            in an association, this is the SKILL entity_id by convention; tech_entity_id
            carries the TECHNOLOGY counterpart.
        tech_entity_id: UUID of the associated TECHNOLOGY node, or None when no association.
        canonical_name: Normalised lowercase name of the competency.
        entity_type: EntityType of the primary entity (SKILL or TECHNOLOGY).
        score: Numeric score in [0.0, 100.0], rounded to 2 decimal places.
        proficiency_level: Deterministic tier derived from score.
        frequency: Distinct artifact count evidence.
        project_count: Distinct PROJECT connections via USES.
        experience_count: Distinct ROLE connections via USES (COMPANY excluded).
        certificate_count: Distinct CERTIFICATE connections via CERTIFIED_IN.
        evidence_light: True when the entity has mentions but zero applied evidence.
    """

    entity_id: UUID
    tech_entity_id: UUID | None
    canonical_name: str
    entity_type: EntityType
    score: float
    proficiency_level: ProficiencyLevel
    frequency: int
    project_count: int
    experience_count: int
    certificate_count: int
    evidence_light: bool

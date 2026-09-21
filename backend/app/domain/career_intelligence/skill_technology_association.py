"""SkillTechnologyAssociation — logical competency grouping of equivalent SKILL and TECHNOLOGY nodes.

Graph identity is NEVER mutated. Both underlying entity IDs are retained for audit and evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.career_intelligence.career_intelligence_constants import EVIDENCE_LIGHT_MIN_FREQUENCY


@dataclass(frozen=True)
class SkillTechnologyAssociation:
    """Immutable logical grouping of a SKILL and/or TECHNOLOGY node sharing the same canonical name.

    This is a query-time, in-memory construct only. It is never persisted to the database.
    Both underlying entity IDs are preserved so callers can trace evidence back to the
    original graph nodes.

    Attributes:
        competency_name: The shared canonical name (e.g. "python"). Always identical across
            any associated SKILL and TECHNOLOGY pair.
        skill_entity_id: UUID of the SKILL graph_entities row, or None if no SKILL node exists.
        tech_entity_id: UUID of the TECHNOLOGY graph_entities row, or None if no TECHNOLOGY node.
        frequency: max(skill.frequency, tech.frequency) — prevents double-counting cross-artifact
            mentions. If only one entity exists, equals that entity's frequency.
        project_count: Count of distinct PROJECT nodes reachable via USES from either entity ID
            (union, not sum).
        experience_count: Count of distinct ROLE nodes reachable via USES from either entity ID
            (union, not sum). COMPANY nodes are excluded by definition.
        certificate_count: Count of distinct CERTIFICATE nodes reachable via CERTIFIED_IN from
            either entity ID (union, not sum).
        evidence_light: True iff frequency >= 1 AND project_count == 0
            AND experience_count == 0 AND certificate_count == 0.
    """

    competency_name: str
    skill_entity_id: UUID | None
    tech_entity_id: UUID | None
    frequency: int
    project_count: int
    experience_count: int
    certificate_count: int

    @property
    def evidence_light(self) -> bool:
        """Returns True when the competency has artifact mentions but zero applied evidence."""
        return (
            self.frequency >= EVIDENCE_LIGHT_MIN_FREQUENCY
            and self.project_count == 0
            and self.experience_count == 0
            and self.certificate_count == 0
        )

    @property
    def is_associated(self) -> bool:
        """Returns True when both a SKILL and a TECHNOLOGY entity contribute to this competency."""
        return self.skill_entity_id is not None and self.tech_entity_id is not None

"""SkillMetricProfile — raw metric counts for a single SKILL or TECHNOLOGY graph entity."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.career_intelligence.career_intelligence_constants import EVIDENCE_LIGHT_MIN_FREQUENCY
from app.domain.value_objects.entity_type import EntityType


@dataclass(frozen=True)
class SkillMetricProfile:
    """Immutable snapshot of aggregated graph metrics for a single SKILL or TECHNOLOGY entity.

    Attributes:
        entity_id: UUID of the graph_entities row.
        canonical_name: Canonical (normalised, lowercase, stripped) name of the entity.
        entity_type: EntityType.SKILL or EntityType.TECHNOLOGY — as stored in the graph.
            Never coerced or reclassified; always the value supplied by the LLM extractor.
        frequency: COUNT(DISTINCT artifact_id) across entity_artifact_provenance for this entity.
        project_count: COUNT(DISTINCT source_entity_id) of USES edges where the source is a PROJECT.
        experience_count: COUNT(DISTINCT source_entity_id) of USES edges where the source is a ROLE.
            COMPANY nodes are explicitly excluded. This is the sole definition of experience_count.
        certificate_count: COUNT(DISTINCT source_entity_id) of CERTIFIED_IN edges where source is CERTIFICATE.
        evidence_light: True iff frequency >= EVIDENCE_LIGHT_MIN_FREQUENCY
            AND project_count == 0 AND experience_count == 0 AND certificate_count == 0.
    """

    entity_id: UUID
    canonical_name: str
    entity_type: EntityType
    frequency: int
    project_count: int
    experience_count: int
    certificate_count: int

    @property
    def evidence_light(self) -> bool:
        """Returns True when the entity has artifact mentions but zero applied evidence.

        Definition: frequency >= 1 AND project_count == 0 AND experience_count == 0
            AND certificate_count == 0.
        """
        return (
            self.frequency >= EVIDENCE_LIGHT_MIN_FREQUENCY
            and self.project_count == 0
            and self.experience_count == 0
            and self.certificate_count == 0
        )

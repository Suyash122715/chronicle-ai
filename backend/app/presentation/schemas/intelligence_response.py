"""Pydantic v2 response schemas for Career Intelligence endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.application.career_intelligence.get_career_insights_use_case import CareerInsights
from app.domain.career_intelligence.skill_score import SkillScore


class SkillScoreResponse(BaseModel):
    """Pydantic schema representing a scored skill or technology competency."""

    model_config = ConfigDict(from_attributes=False)

    entity_id: UUID
    tech_entity_id: UUID | None = None
    canonical_name: str
    entity_type: str
    score: float
    proficiency_level: str
    frequency: int
    project_count: int
    experience_count: int
    certificate_count: int
    evidence_light: bool

    @classmethod
    def from_domain(cls, score: SkillScore) -> "SkillScoreResponse":
        return cls(
            entity_id=score.entity_id,
            tech_entity_id=score.tech_entity_id,
            canonical_name=score.canonical_name,
            entity_type=score.entity_type.value,
            score=score.score,
            proficiency_level=score.proficiency_level.value,
            frequency=score.frequency,
            project_count=score.project_count,
            experience_count=score.experience_count,
            certificate_count=score.certificate_count,
            evidence_light=score.evidence_light,
        )


class SkillScoreListResponse(BaseModel):
    """Collection response containing scored competencies."""

    model_config = ConfigDict(from_attributes=False)

    items: list[SkillScoreResponse] = Field(default_factory=list)
    total: int = 0


class CareerInsightsResponse(BaseModel):
    """Summary and high-level metrics for a user's career profile."""

    model_config = ConfigDict(from_attributes=False)

    total_competencies: int
    top_skills: list[SkillScoreResponse] = Field(default_factory=list)
    evidence_light_count: int
    evidence_light_skills: list[SkillScoreResponse] = Field(default_factory=list)
    expert_count: int
    advanced_count: int
    intermediate_count: int
    beginner_count: int

    @classmethod
    def from_domain(cls, insights: CareerInsights) -> "CareerInsightsResponse":
        return cls(
            total_competencies=insights.total_competencies,
            top_skills=[SkillScoreResponse.from_domain(s) for s in insights.top_skills],
            evidence_light_count=insights.evidence_light_count,
            evidence_light_skills=[
                SkillScoreResponse.from_domain(s) for s in insights.evidence_light_skills
            ],
            expert_count=insights.expert_count,
            advanced_count=insights.advanced_count,
            intermediate_count=insights.intermediate_count,
            beginner_count=insights.beginner_count,
        )

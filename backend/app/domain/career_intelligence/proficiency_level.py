"""ProficiencyLevel — deterministic proficiency tier for a scored skill/technology."""

from enum import Enum

from app.domain.career_intelligence.career_intelligence_constants import (
    PROFICIENCY_ADVANCED_MAX,
    PROFICIENCY_BEGINNER_MAX,
    PROFICIENCY_INTERMEDIATE_MAX,
)


class ProficiencyLevel(str, Enum):
    """Deterministic proficiency classification derived from a numeric score in [0.0, 100.0].

    Thresholds (from career_intelligence_constants):
        BEGINNER:      0.0  ≤ score < 25.0
        INTERMEDIATE: 25.0  ≤ score < 55.0
        ADVANCED:     55.0  ≤ score < 80.0
        EXPERT:       80.0  ≤ score ≤ 100.0
    """

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

    @classmethod
    def from_score(cls, score: float) -> "ProficiencyLevel":
        """Derives a ProficiencyLevel from a numeric score in [0.0, 100.0].

        Args:
            score: Numeric score in the range [0.0, 100.0].

        Returns:
            The corresponding ProficiencyLevel enum member.

        Raises:
            ValueError: If score is outside the valid range [0.0, 100.0].
        """
        if not (0.0 <= score <= 100.0):
            raise ValueError(f"Score {score} is outside the valid range [0.0, 100.0].")
        if score < PROFICIENCY_BEGINNER_MAX:
            return cls.BEGINNER
        if score < PROFICIENCY_INTERMEDIATE_MAX:
            return cls.INTERMEDIATE
        if score < PROFICIENCY_ADVANCED_MAX:
            return cls.ADVANCED
        return cls.EXPERT

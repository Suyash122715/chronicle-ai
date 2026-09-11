"""Entity type domain enumeration."""

from enum import Enum


class EntityType(str, Enum):
    """Enumeration of knowledge graph entity types."""

    SKILL = "SKILL"
    PROJECT = "PROJECT"
    COMPANY = "COMPANY"
    TECHNOLOGY = "TECHNOLOGY"
    CERTIFICATE = "CERTIFICATE"
    INSTITUTION = "INSTITUTION"
    ACHIEVEMENT = "ACHIEVEMENT"
    ROLE = "ROLE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, val: str) -> "EntityType":
        """Coerces a string value to an EntityType enum case-insensitively."""
        if not val or not isinstance(val, str):
            return cls.UNKNOWN
        clean_val = val.strip().upper()
        for item in cls:
            if item.value == clean_val:
                return item
        return cls.UNKNOWN

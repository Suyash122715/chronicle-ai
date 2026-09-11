"""Relationship type domain enumeration."""

from enum import Enum


class RelationshipType(str, Enum):
    """Enumeration of knowledge graph relationship types."""

    LEARNED = "LEARNED"
    WORKED_AT = "WORKED_AT"
    CREATED = "CREATED"
    USES = "USES"
    CERTIFIED_IN = "CERTIFIED_IN"
    STUDIED_AT = "STUDIED_AT"
    HELD_ROLE = "HELD_ROLE"
    ISSUED_BY = "ISSUED_BY"
    RELATED_TO = "RELATED_TO"

    @classmethod
    def from_string(cls, val: str) -> "RelationshipType":
        """Coerces a string value to a RelationshipType enum case-insensitively."""
        if not val or not isinstance(val, str):
            raise ValueError(f"Invalid relationship type string: {val}")
        clean_val = val.strip().upper()
        for item in cls:
            if item.value == clean_val:
                return item
        raise ValueError(f"Unsupported relationship type: {val}")

"""DocumentType domain value object representation."""

from enum import Enum
from typing import Self


class DocumentTypeEnum(str, Enum):
    """Supported document type enumerations for persistence and domain categorization."""

    RESUME = "Resume"
    CERTIFICATE = "Certificate"
    MARKSHEET = "Marksheet"
    INTERNSHIP_LETTER = "Internship Letter"
    PROJECT_REPORT = "Project Report"
    GITHUB_REPOSITORY = "GitHub Repository"
    PORTFOLIO = "Portfolio"
    UNKNOWN = "Unknown"


class DocumentType:
    """Domain Value Object wrapping DocumentTypeEnum.

    Encapsulates document type domain logic and prevents stringly-typed usage.
    """

    __slots__ = ("_type_enum",)

    def __init__(self, type_enum: DocumentTypeEnum) -> None:
        if not isinstance(type_enum, DocumentTypeEnum):
            raise TypeError(f"Expected DocumentTypeEnum, got {type(type_enum).__name__}")
        self._type_enum = type_enum

    @property
    def value(self) -> str:
        """Returns the string representation of the document type."""
        return self._type_enum.value

    @property
    def enum_value(self) -> DocumentTypeEnum:
        """Returns the underlying DocumentTypeEnum."""
        return self._type_enum

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Constructs a DocumentType value object from a string.

        Case-insensitive matching; falls back to UNKNOWN if invalid.
        """
        if not value:
            return cls(DocumentTypeEnum.UNKNOWN)

        normalized = value.strip().lower()
        for item in DocumentTypeEnum:
            if item.value.lower() == normalized or item.name.lower() == normalized:
                return cls(item)
        return cls(DocumentTypeEnum.UNKNOWN)

    @classmethod
    def resume(cls) -> Self:
        return cls(DocumentTypeEnum.RESUME)

    @classmethod
    def certificate(cls) -> Self:
        return cls(DocumentTypeEnum.CERTIFICATE)

    @classmethod
    def marksheet(cls) -> Self:
        return cls(DocumentTypeEnum.MARKSHEET)

    @classmethod
    def internship_letter(cls) -> Self:
        return cls(DocumentTypeEnum.INTERNSHIP_LETTER)

    @classmethod
    def project_report(cls) -> Self:
        return cls(DocumentTypeEnum.PROJECT_REPORT)

    @classmethod
    def github_repository(cls) -> Self:
        return cls(DocumentTypeEnum.GITHUB_REPOSITORY)

    @classmethod
    def portfolio(cls) -> Self:
        return cls(DocumentTypeEnum.PORTFOLIO)

    @classmethod
    def unknown(cls) -> Self:
        return cls(DocumentTypeEnum.UNKNOWN)

    def is_known(self) -> bool:
        """Returns True if the document type is not UNKNOWN."""
        return self._type_enum != DocumentTypeEnum.UNKNOWN

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DocumentType):
            return self._type_enum == other._type_enum
        if isinstance(other, DocumentTypeEnum):
            return self._type_enum == other
        if isinstance(other, str):
            return self.value.lower() == other.strip().lower()
        return False

    def __hash__(self) -> int:
        return hash(self._type_enum)

    def __repr__(self) -> str:
        return f"DocumentType(value={self.value!r})"

    def __str__(self) -> str:
        return self.value

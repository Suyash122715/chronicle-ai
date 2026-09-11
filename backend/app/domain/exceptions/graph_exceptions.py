"""Knowledge Graph domain exceptions."""

from app.domain.exceptions.base import DomainException


class GraphEntityNotFoundError(DomainException):
    """Raised when a requested knowledge graph entity is not found or does not belong to the user."""

    def __init__(self, message: str = "Knowledge graph entity not found.") -> None:
        super().__init__(message)


class GraphRelationshipNotFoundError(DomainException):
    """Raised when a requested knowledge graph relationship is not found."""

    def __init__(self, message: str = "Knowledge graph relationship not found.") -> None:
        super().__init__(message)

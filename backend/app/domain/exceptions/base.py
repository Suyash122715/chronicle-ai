"""Base exception definitions for the domain layer."""


class DomainException(Exception):
    """Base exception class for all business domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityNotFoundError(DomainException):
    """Raised when a requested domain entity cannot be located."""

    def __init__(self, entity_name: str, entity_id: str) -> None:
        message = f"{entity_name} with ID '{entity_id}' was not found."
        super().__init__(message)
        self.entity_name = entity_name
        self.entity_id = entity_id


class DomainValidationError(DomainException):
    """Raised when a domain rule validation fails."""
    pass

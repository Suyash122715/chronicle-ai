"""Domain exceptions package."""

from app.domain.exceptions.base import DomainException, EntityNotFoundError, DomainValidationError

__all__ = ["DomainException", "EntityNotFoundError", "DomainValidationError"]

"""Domain exceptions package."""

from app.domain.exceptions.base import (
    DomainException,
    EntityNotFoundError,
    DomainValidationError,
)
from app.domain.exceptions.user_exceptions import (
    UserAlreadyExistsError,
    InvalidEmailFormatError,
    PasswordTooWeakError,
)
from app.domain.exceptions.auth_exceptions import InvalidCredentialsError, InvalidTokenError

__all__ = [
    "DomainException",
    "EntityNotFoundError",
    "DomainValidationError",
    "UserAlreadyExistsError",
    "InvalidEmailFormatError",
    "PasswordTooWeakError",
    "InvalidCredentialsError",
    "InvalidTokenError",
]

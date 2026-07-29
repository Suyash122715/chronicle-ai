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
from app.domain.exceptions.artifact_exceptions import (
    ArtifactNotFoundError,
    FileTooLargeError,
    UnsupportedMediaTypeError,
    StorageError,
)

__all__ = [
    "DomainException",
    "EntityNotFoundError",
    "DomainValidationError",
    "UserAlreadyExistsError",
    "InvalidEmailFormatError",
    "PasswordTooWeakError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "ArtifactNotFoundError",
    "FileTooLargeError",
    "UnsupportedMediaTypeError",
    "StorageError",
]

"""User domain exceptions."""

from app.domain.exceptions.base import DomainException, DomainValidationError


class UserAlreadyExistsError(DomainException):
    """Raised when a user registration attempt uses an already registered email address."""

    def __init__(self, email: str) -> None:
        message = f"User with email '{email}' already exists."
        super().__init__(message)
        self.email = email


class InvalidEmailFormatError(DomainValidationError):
    """Raised when an email address format is invalid."""

    def __init__(self, email: str) -> None:
        message = f"Invalid email format: '{email}'."
        super().__init__(message)
        self.email = email


class PasswordTooWeakError(DomainValidationError):
    """Raised when a password fails strength validation rules."""

    def __init__(self, reason: str = "Password must be at least 8 characters long.") -> None:
        super().__init__(reason)
        self.reason = reason

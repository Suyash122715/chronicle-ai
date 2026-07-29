"""Authentication-related domain exceptions."""

from app.domain.exceptions.base import DomainException


class InvalidCredentialsError(DomainException):
    """Raised when login credentials cannot be verified.

    Deliberately uses a generic message that does not indicate whether
    the email or the password was incorrect, to prevent user-enumeration attacks.
    """

    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class InvalidTokenError(DomainException):
    """Raised when a JWT token cannot be decoded, is expired, or has been tampered with."""

    def __init__(self, reason: str = "Token is invalid or has expired.") -> None:
        super().__init__(reason)


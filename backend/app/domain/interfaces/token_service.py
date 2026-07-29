"""Token service interface — defines the contract for JWT token operations.

Placing the interface in the domain layer ensures that the Application layer
can depend on this abstraction without importing any JWT library directly.
A concrete implementation lives in infrastructure, which can be replaced
with any other token mechanism (e.g. Paseto, opaque tokens) without touching
Application or Domain code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TokenPayload:
    """Value object representing the verified claims of a decoded JWT token."""

    subject: str          # User UUID as string
    expires_at: datetime  # Token expiry UTC datetime


class TokenServiceInterface(ABC):
    """Abstract interface for access token creation and verification."""

    @abstractmethod
    def create_access_token(self, subject: str) -> str:
        """Creates a signed access token for the given user subject (UUID string).

        Args:
            subject: The user's UUID as a string, stored in the JWT 'sub' claim.

        Returns:
            str: Encoded, signed JWT access token string.
        """
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> TokenPayload:
        """Decodes and verifies a signed access token.

        Args:
            token: Encoded JWT string.

        Returns:
            TokenPayload: Verified claims including subject and expiry.

        Raises:
            InvalidTokenError: If the token is invalid, expired, or tampered with.
        """
        pass

    # TODO: Add create_refresh_token / decode_refresh_token in Phase 2.3

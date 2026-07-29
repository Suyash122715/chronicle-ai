"""Token Service placeholder for JWT access and refresh token management."""


class TokenService:
    """Service for encoding, decoding, and verifying JWT tokens."""

    def create_access_token(self, subject: str) -> str:
        """Creates a JWT access token for a given user subject."""
        # TODO: Implement JWT encoding in Phase 2.
        raise NotImplementedError("TokenService not implemented yet.")

    def verify_token(self, token: str) -> str:
        """Verifies JWT token signature and returns subject user ID."""
        # TODO: Implement JWT verification in Phase 2.
        raise NotImplementedError("TokenService not implemented yet.")

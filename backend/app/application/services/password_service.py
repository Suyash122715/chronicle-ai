"""Password Service placeholder for hashing and password comparison."""


class PasswordService:
    """Service for secure password hashing and verification using bcrypt."""

    def hash_password(self, password: str) -> str:
        """Returns bcrypt password hash."""
        # TODO: Implement bcrypt hashing in Phase 2.
        raise NotImplementedError("PasswordService not implemented yet.")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies plain text password against stored bcrypt hash."""
        # TODO: Implement bcrypt verification in Phase 2.
        raise NotImplementedError("PasswordService not implemented yet.")

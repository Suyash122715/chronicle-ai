"""Argon2 password hashing service implementation using argon2-cffi."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError


class PasswordService:
    """Service providing secure password hashing and verification using Argon2id."""

    def __init__(self) -> None:
        self._ph = PasswordHasher()

    def hash_password(self, password: str) -> str:
        """Hashes a plain text password using Argon2id.
        
        Args:
            password: Plain text password string.
            
        Returns:
            str: Secure Argon2 password hash.
        """
        return self._ph.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain text password against an Argon2 hash.
        
        Args:
            plain_password: Plain text password string.
            hashed_password: Argon2 hash string stored in database.
            
        Returns:
            bool: True if password matches hash, False otherwise.
        """
        try:
            return self._ph.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError):
            return False

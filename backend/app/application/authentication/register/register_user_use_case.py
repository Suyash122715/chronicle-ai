"""Register User Use Case implementation."""

from email_validator import validate_email, EmailNotValidError

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    UserAlreadyExistsError,
    InvalidEmailFormatError,
    PasswordTooWeakError,
)
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_service import PasswordService


class RegisterUserUseCase:
    """Application use case for registering new user accounts.
    
    Contains business logic for credential validation, uniqueness verification,
    Argon2 password hashing, and user entity creation.
    """

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordService,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service

    async def execute(self, email: str, password: str, full_name: str) -> User:
        """Executes the user registration workflow.
        
        Args:
            email: Raw user email address input.
            password: Plain text password input.
            full_name: User full name.
            
        Returns:
            User: Created pure domain user entity.
            
        Raises:
            InvalidEmailFormatError: If email format is invalid.
            PasswordTooWeakError: If password is less than 8 characters.
            UserAlreadyExistsError: If email is already registered.
        """
        # 1. Validate & normalize email format
        normalized_email = self._validate_and_normalize_email(email)

        # 2. Validate password strength
        self._validate_password_strength(password)

        # 3. Check for existing user email conflict
        if await self._user_repository.exists_by_email(normalized_email):
            raise UserAlreadyExistsError(normalized_email)

        # 4. Hash password securely using Argon2
        password_hash = self._password_service.hash_password(password)

        # 5. Create domain User entity
        user = User(
            email=normalized_email,
            password_hash=password_hash,
            full_name=full_name.strip(),
        )

        # 6. Persist user via repository
        created_user = await self._user_repository.add(user)

        # TODO: Add Phase 2.2 JWT Token Generation & Event Notification after user registration
        # TODO: Add Phase 2.3 Verification Email Dispatch

        return created_user

    def _validate_and_normalize_email(self, email: str) -> str:
        """Normalizes and validates email string using email-validator."""
        clean_email = email.strip().lower()
        if not clean_email:
            raise InvalidEmailFormatError(email)
        try:
            valid_info = validate_email(clean_email, check_deliverability=False)
            return valid_info.normalized
        except EmailNotValidError:
            raise InvalidEmailFormatError(email)

    def _validate_password_strength(self, password: str) -> None:
        """Validates password strength rules (minimum 8 characters)."""
        if not password or len(password) < 8:
            raise PasswordTooWeakError("Password must be at least 8 characters long.")

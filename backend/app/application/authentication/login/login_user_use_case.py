"""Login User Use Case implementation."""

from app.domain.exceptions.auth_exceptions import InvalidCredentialsError
from app.domain.interfaces.token_service import TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_service import PasswordService


class LoginResult:
    """Value object returned by the login use case."""

    __slots__ = ("access_token", "token_type")

    def __init__(self, access_token: str, token_type: str = "bearer") -> None:
        self.access_token = access_token
        self.token_type = token_type


class LoginUserUseCase:
    """Application use case for authenticating a user and issuing a JWT access token.

    Business rules enforced here:
    - Email is normalized before lookup.
    - An identical error is returned whether the email does not exist or the
      password is wrong (prevents user-enumeration attacks).
    - Only active users may log in.
    - Token creation is delegated to TokenServiceInterface so the JWT
      implementation can be swapped without modifying this class.
    """

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordService,
        token_service: TokenServiceInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._token_service = token_service

    async def execute(self, email: str, password: str) -> LoginResult:
        """Authenticates a user and returns a JWT access token on success.

        Args:
            email: Raw email address from the login request.
            password: Plain text password from the login request.

        Returns:
            LoginResult: Contains the signed access token and token type.

        Raises:
            InvalidCredentialsError: If email is not found, password is wrong,
                or the account is inactive. Always uses the same generic message
                to prevent user-enumeration.
        """
        # 1. Normalize email (same normalization used at registration)
        normalized_email = email.strip().lower()

        # 2. Look up user — return generic error if not found
        user = await self._user_repository.get_by_email(normalized_email)
        if user is None:
            raise InvalidCredentialsError()

        # 3. Verify password — return generic error if wrong
        if not self._password_service.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        # 4. Reject inactive accounts
        if not user.is_active:
            raise InvalidCredentialsError()

        # 5. Issue access token
        access_token = self._token_service.create_access_token(subject=str(user.id))

        # TODO: Issue refresh token and persist it in Phase 2.3
        # TODO: Record last login timestamp in Phase 2.3
        return LoginResult(access_token=access_token)

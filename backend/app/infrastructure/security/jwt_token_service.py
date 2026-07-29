"""PyJWT-backed concrete implementation of TokenServiceInterface."""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError as PyJWTInvalidTokenError

from app.config import settings
from app.domain.exceptions.auth_exceptions import InvalidTokenError
from app.domain.interfaces.token_service import TokenPayload, TokenServiceInterface


class JWTTokenService(TokenServiceInterface):
    """Concrete JWT service using PyJWT with HS256 signing.

    The algorithm, secret, and expiry are read from application Settings so
    they can be rotated without touching this class. The concrete class lives
    in Infrastructure; callers depend only on TokenServiceInterface.
    """

    def create_access_token(self, subject: str) -> str:
        """Encodes a HS256-signed JWT access token with 'sub' and 'exp' claims.

        Args:
            subject: The user UUID string to embed in the 'sub' claim.

        Returns:
            str: Signed JWT access token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": subject,
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> TokenPayload:
        """Decodes and validates a JWT access token.

        Args:
            token: Encoded JWT string.

        Returns:
            TokenPayload: Verified subject and expiry claims.

        Raises:
            InvalidTokenError: If token is expired, tampered with, or malformed.
        """
        try:
            decoded = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except ExpiredSignatureError:
            raise InvalidTokenError("Access token has expired.")
        except PyJWTInvalidTokenError:
            raise InvalidTokenError("Access token is invalid.")

        subject = decoded.get("sub")
        exp = decoded.get("exp")

        if not subject or not exp:
            raise InvalidTokenError("Access token is missing required claims.")

        return TokenPayload(
            subject=subject,
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )

    # TODO: Implement create_refresh_token and decode_refresh_token in Phase 2.3

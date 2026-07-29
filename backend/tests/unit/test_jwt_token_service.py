"""Unit tests for JWTTokenService."""

from datetime import datetime, timezone
import pytest

from app.domain.exceptions.auth_exceptions import InvalidTokenError
from app.infrastructure.security.jwt_token_service import JWTTokenService


def test_create_and_decode_access_token_success() -> None:
    """Verifies that a JWT access token can be created and correctly decoded."""
    token_service = JWTTokenService()
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token = token_service.create_access_token(subject=user_id)
    assert isinstance(token, str)
    assert len(token) > 0

    payload = token_service.decode_access_token(token)
    assert payload.subject == user_id
    assert payload.expires_at > datetime.now(timezone.utc)


def test_decode_invalid_jwt_token_raises_invalid_token_error() -> None:
    """Verifies that decoding a malformed or invalid JWT token raises InvalidTokenError."""
    token_service = JWTTokenService()

    with pytest.raises(InvalidTokenError) as exc_info:
        token_service.decode_access_token("invalid.jwt.token")

    assert "Access token is invalid" in str(exc_info.value)

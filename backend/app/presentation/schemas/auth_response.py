"""Authentication response schemas using Pydantic v2."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """User profile response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class RegisterUserResponse(BaseModel):
    """Response payload schema for successful user registration."""

    user: UserResponse
    message: str = "User registered successfully."


class TokenResponse(BaseModel):
    """Response payload for a successful login — returns the JWT access token."""

    access_token: str
    token_type: str = "bearer"

# TODO: Add refresh_token field to TokenResponse in Phase 2.3
# TODO: Add expires_in (seconds) field to TokenResponse in Phase 2.3

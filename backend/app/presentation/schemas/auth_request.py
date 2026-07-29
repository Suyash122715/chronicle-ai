"""Authentication request schemas using Pydantic v2."""

from pydantic import BaseModel, EmailStr, Field


class RegisterUserRequest(BaseModel):
    """Request payload schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        description="User password (minimum 8 characters)",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User full name",
    )


class LoginRequest(BaseModel):
    """Request payload schema for user login."""

    email: EmailStr = Field(..., description="Registered user email address")
    password: str = Field(..., description="User password")

# TODO: Add Phase 2.3 RefreshTokenRequest schema (refresh_token)
# TODO: Add Phase 2.4 ResetPasswordRequest schema (token, new_password)

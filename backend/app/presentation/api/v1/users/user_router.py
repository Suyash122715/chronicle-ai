"""User profile router containing user-related endpoints."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user
from app.domain.entities.user import User
from app.presentation.schemas.auth_response import UserResponse

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Get Current Authenticated User",
    description="Retrieves the profile information of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Handles GET /api/v1/users/me.

    Requires a valid JWT Bearer token. Returns the authenticated user's profile details.
    """
    return UserResponse.model_validate(current_user)


# TODO: Add PATCH /users/me in future user profile phase

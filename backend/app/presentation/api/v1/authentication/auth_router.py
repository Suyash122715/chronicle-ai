"""Authentication router containing user registration and login endpoints."""

from fastapi import APIRouter, Depends, status

from app.application.authentication.login.login_user_use_case import LoginUserUseCase
from app.application.authentication.register.register_user_use_case import RegisterUserUseCase
from app.dependencies import get_login_user_use_case, get_register_user_use_case
from app.presentation.schemas.auth_request import LoginRequest, RegisterUserRequest
from app.presentation.schemas.auth_response import RegisterUserResponse, TokenResponse, UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterUserResponse,
    summary="User Registration",
    description="Registers a new user account with unique email and hashed password.",
)
async def register_user(
    payload: RegisterUserRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
) -> RegisterUserResponse:
    """Handles POST /api/v1/auth/register.

    Delegates credential validation, Argon2 hashing, and persistence to RegisterUserUseCase.
    """
    user = await use_case.execute(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return RegisterUserResponse(
        user=UserResponse.model_validate(user),
        message="User registered successfully.",
    )


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticates a user and returns a JWT access token.",
)
async def login_user(
    payload: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_user_use_case),
) -> TokenResponse:
    """Handles POST /api/v1/auth/login.

    Delegates credential verification and token generation to LoginUserUseCase.
    Returns 401 for any invalid credential combination without revealing specifics.
    """
    result = await use_case.execute(
        email=payload.email,
        password=payload.password,
    )
    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
    )


# TODO: Implement POST /auth/logout (token blacklist / session invalidation) in Phase 2.3
# TODO: Implement POST /auth/refresh (refresh token rotation) in Phase 2.3
# TODO: Implement POST /auth/reset-password (password reset workflow) in Phase 2.4

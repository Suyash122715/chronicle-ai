"""Centralized FastAPI dependency injection providers."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.authentication.login.login_user_use_case import LoginUserUseCase
from app.application.authentication.register.register_user_use_case import RegisterUserUseCase
from app.domain.interfaces.token_service import TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.db.session import get_async_session
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_token_service import JWTTokenService
from app.infrastructure.security.password_service import PasswordService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async SQLAlchemy database sessions.

    Routers MUST NOT instantiate sessions directly; they must request this dependency.
    """
    async for session in get_async_session():
        yield session


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepositoryInterface:
    """Returns concrete SQLAlchemy UserRepository bound to the current request session."""
    return SQLAlchemyUserRepository(session)


def get_password_service() -> PasswordService:
    """Returns the Argon2id password hashing/verification service."""
    return PasswordService()


def get_token_service() -> TokenServiceInterface:
    """Returns the concrete JWT token service.

    Returns TokenServiceInterface so callers remain decoupled from PyJWT.
    Swapping to a different token library requires only changing this factory.
    """
    return JWTTokenService()


def get_register_user_use_case(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
) -> RegisterUserUseCase:
    """Injects dependencies into RegisterUserUseCase."""
    return RegisterUserUseCase(
        user_repository=user_repository,
        password_service=password_service,
    )


def get_login_user_use_case(
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    token_service: TokenServiceInterface = Depends(get_token_service),
) -> LoginUserUseCase:
    """Injects dependencies into LoginUserUseCase."""
    return LoginUserUseCase(
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )

# TODO: Add get_current_user dependency for protected routes in Phase 2.3
# TODO: Add get_refresh_token_use_case in Phase 2.3

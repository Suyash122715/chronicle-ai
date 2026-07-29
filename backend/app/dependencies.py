"""Centralized FastAPI dependency injection providers."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_async_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async SQLAlchemy database sessions.
    
    Provides clean lifecycle management for database sessions injected into use cases/services.
    Routers MUST NOT instantiate sessions directly; they must request this dependency.
    """
    async for session in get_async_session():
        yield session


# TODO: Add Phase 2 Centralized Dependency Providers:
# - get_current_user_id (Authentication dependency)
# - get_artifact_repository (Repository injection)
# - get_user_repository (Repository injection)
# - get_storage_provider (File storage service injection)
# - get_ai_provider (AI service orchestration injection)

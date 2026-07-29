"""Async SQLAlchemy 2 engine and session management configuration."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create async engine for PostgreSQL interaction
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator producing scoped async database sessions.
    
    Yields:
        AsyncSession: Scoped async database session for dependency injection.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

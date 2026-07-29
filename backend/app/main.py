"""FastAPI Application entry point and router initialization."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from app.config import settings
from app.infrastructure.logging.logger import setup_logging, get_logger
from app.presentation.api.v1.health.health_router import health_router
from app.presentation.api.v1.router import api_v1_router
from app.presentation.middleware.error_handler import register_error_handlers
from app.presentation.middleware.logging_middleware import LoggingMiddleware

logger = get_logger("chronicle_ai.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan events."""
    setup_logging()
    logger.info("Initializing Chronicle AI Backend Service (%s)...", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down Chronicle AI Backend Service...")


def create_app() -> FastAPI:
    """Application factory for configuring and returning the FastAPI instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Register HTTP logging middleware
    app.add_middleware(LoggingMiddleware)

    # Register global exception handlers
    register_error_handlers(app)

    # Mount direct GET /health endpoint
    app.include_router(health_router)

    # Mount API v1 Routers (/api/v1/...)
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_app()

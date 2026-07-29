"""Global exception handler converting domain & system exceptions to HTTP error responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions.base import DomainException, EntityNotFoundError, DomainValidationError
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.error_handler")


def register_error_handlers(app: FastAPI) -> None:
    """Registers exception handlers on the FastAPI application instance."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        """Handles entity lookup failures (HTTP 404)."""
        logger.warning("Entity not found on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
        """Handles domain validation failures (HTTP 400)."""
        logger.warning("Domain validation failure on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainException)
    async def base_domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        """Handles generic domain exceptions (HTTP 400)."""
        logger.warning("Domain exception on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handles unexpected failures without exposing internal stack traces (HTTP 500)."""
        logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        )

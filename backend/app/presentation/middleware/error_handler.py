"""Global exception handler converting domain & system exceptions to HTTP error responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions.artifact_exceptions import (
    ArtifactNotFoundError,
    ExtractionNotFoundError,
    FileTooLargeError,
    StorageError,
    UnsupportedMediaTypeError,
)
from app.domain.exceptions.auth_exceptions import InvalidCredentialsError, InvalidTokenError
from app.domain.exceptions.base import DomainException, DomainValidationError, EntityNotFoundError
from app.domain.exceptions.user_exceptions import UserAlreadyExistsError
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.error_handler")


def register_error_handlers(app: FastAPI) -> None:
    """Registers exception handlers on the FastAPI application instance."""

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
        """Handles invalid login credentials (HTTP 401 Unauthorized)."""
        logger.warning("Failed login attempt on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError) -> JSONResponse:
        """Handles invalid or expired JWT tokens (HTTP 401 Unauthorized)."""
        logger.warning("Invalid token on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
        """Handles duplicate user registration attempts (HTTP 409 Conflict)."""
        logger.warning("Duplicate user registration attempt on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @app.exception_handler(ArtifactNotFoundError)
    async def artifact_not_found_handler(request: Request, exc: ArtifactNotFoundError) -> JSONResponse:
        """Handles artifact lookup / ownership failures (HTTP 404 Not Found)."""
        logger.warning("Artifact not found on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(ExtractionNotFoundError)
    async def extraction_not_found_handler(request: Request, exc: ExtractionNotFoundError) -> JSONResponse:
        """Handles extraction lookup failures (HTTP 404 Not Found)."""
        logger.warning("Extraction not found on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError) -> JSONResponse:
        """Handles file size limit exceedance (HTTP 400 Bad Request)."""
        logger.warning("File too large on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(UnsupportedMediaTypeError)
    async def unsupported_media_type_handler(request: Request, exc: UnsupportedMediaTypeError) -> JSONResponse:
        """Handles unsupported upload media types (HTTP 415 Unsupported Media Type)."""
        logger.warning("Unsupported media type on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={"detail": exc.message},
        )

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
        """Handles internal file storage operation failures (HTTP 500 Internal Server Error)."""
        logger.error("Storage error on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        """Handles entity lookup failures (HTTP 404 Not Found)."""
        logger.warning("Entity not found on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
        """Handles domain validation failures (HTTP 400 Bad Request)."""
        logger.warning("Domain validation failure on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainException)
    async def base_domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        """Handles generic domain exceptions (HTTP 400 Bad Request)."""
        logger.warning("Domain exception on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handles unexpected failures without exposing internal stack traces (HTTP 500 Internal Server Error)."""
        logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        )

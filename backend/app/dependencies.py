"""Centralized FastAPI dependency injection providers."""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import BackgroundTasks, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.artifacts.delete.delete_artifact_use_case import DeleteArtifactUseCase
from app.application.artifacts.get.get_artifact_use_case import GetArtifactUseCase
from app.application.artifacts.list.list_artifacts_use_case import ListArtifactsUseCase
from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase
from app.application.artifacts.upload.upload_artifact_use_case import UploadArtifactUseCase
from app.application.authentication.login.login_user_use_case import LoginUserUseCase
from app.application.authentication.register.register_user_use_case import RegisterUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidTokenError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.background_job_service import BackgroundJobServiceInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.domain.interfaces.text_extractor import TextExtractorInterface
from app.domain.interfaces.token_service import TokenPayload, TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.document_type import DocumentTypeEnum
from app.infrastructure.db.session import get_async_session
from app.infrastructure.jobs.fastapi_background_job_service import FastAPIBackgroundJobService
from app.infrastructure.processing.deterministic_classifier import DeterministicDocumentClassifier
from app.infrastructure.processing.placeholders import (
    CertificateExtractor,
    GitHubRepositoryExtractor,
    InternshipLetterExtractor,
    MarksheetExtractor,
    PortfolioExtractor,
    ProjectReportExtractor,
    ResumeExtractor,
    UnknownExtractor,
)
from app.infrastructure.processing.text_extractor import DefaultTextExtractor
from app.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_token_service import JWTTokenService
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.storage.local_storage_service import LocalStorageService

# Security scheme for Bearer token extraction
http_bearer = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async SQLAlchemy database sessions."""
    async for session in get_async_session():
        yield session


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepositoryInterface:
    """Returns concrete SQLAlchemy UserRepository bound to the current request session."""
    return SQLAlchemyUserRepository(session)


def get_artifact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ArtifactRepositoryInterface:
    """Returns concrete SQLAlchemy ArtifactRepository bound to the current request session."""
    return SQLAlchemyArtifactRepository(session)


def get_storage_service() -> StorageServiceInterface:
    """Returns concrete LocalStorageService."""
    return LocalStorageService()


def get_text_extractor() -> TextExtractorInterface:
    """Returns concrete DefaultTextExtractor."""
    return DefaultTextExtractor()


def get_document_classifier() -> DocumentClassifierInterface:
    """Returns concrete DeterministicDocumentClassifier provider."""
    return DeterministicDocumentClassifier()


def get_extractor_registry() -> ExtractorRegistry:
    """Returns ExtractorRegistry initialized with placeholder extractors."""
    registry = ExtractorRegistry(default_extractor=UnknownExtractor)
    registry.register(DocumentTypeEnum.RESUME, ResumeExtractor)
    registry.register(DocumentTypeEnum.CERTIFICATE, CertificateExtractor)
    registry.register(DocumentTypeEnum.MARKSHEET, MarksheetExtractor)
    registry.register(DocumentTypeEnum.INTERNSHIP_LETTER, InternshipLetterExtractor)
    registry.register(DocumentTypeEnum.PROJECT_REPORT, ProjectReportExtractor)
    registry.register(DocumentTypeEnum.PORTFOLIO, PortfolioExtractor)
    registry.register(DocumentTypeEnum.GITHUB_REPOSITORY, GitHubRepositoryExtractor)
    registry.register(DocumentTypeEnum.UNKNOWN, UnknownExtractor)
    return registry


def get_background_job_service(
    background_tasks: BackgroundTasks = None,
) -> BackgroundJobServiceInterface:
    """Returns concrete FastAPIBackgroundJobService."""
    return FastAPIBackgroundJobService(background_tasks=background_tasks)


def get_password_service() -> PasswordService:
    """Returns the Argon2id password hashing/verification service."""
    return PasswordService()


def get_token_service() -> TokenServiceInterface:
    """Returns the concrete JWT token service."""
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


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    token_service: TokenServiceInterface = Depends(get_token_service),
) -> TokenPayload:
    """Authentication dependency validating the Bearer access token."""
    if not credentials or not credentials.credentials:
        raise InvalidTokenError("Authentication credentials were not provided.")

    return token_service.decode_access_token(credentials.credentials)


async def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
    user_repository: UserRepositoryInterface = Depends(get_user_repository),
) -> User:
    """Authentication & Authorization dependency retrieving the current active user."""
    try:
        user_id = UUID(payload.subject)
    except (ValueError, TypeError):
        raise InvalidTokenError("Invalid user ID in token.")

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError("User account not found or inactive.")

    return user


def get_process_artifact_use_case(
    artifact_repository: ArtifactRepositoryInterface = Depends(get_artifact_repository),
    storage_service: StorageServiceInterface = Depends(get_storage_service),
    document_classifier: DocumentClassifierInterface = Depends(get_document_classifier),
) -> ProcessArtifactUseCase:
    """Injects dependencies into ProcessArtifactUseCase."""
    return ProcessArtifactUseCase(
        artifact_repository=artifact_repository,
        storage_service=storage_service,
        document_classifier=document_classifier,
    )


def get_upload_artifact_use_case(
    artifact_repository: ArtifactRepositoryInterface = Depends(get_artifact_repository),
    storage_service: StorageServiceInterface = Depends(get_storage_service),
    background_job_service: BackgroundJobServiceInterface = Depends(get_background_job_service),
    process_artifact_use_case: ProcessArtifactUseCase = Depends(get_process_artifact_use_case),
) -> UploadArtifactUseCase:
    """Injects dependencies into UploadArtifactUseCase."""
    return UploadArtifactUseCase(
        artifact_repository=artifact_repository,
        storage_service=storage_service,
        background_job_service=background_job_service,
        process_task=process_artifact_use_case.execute,
    )


def get_list_artifacts_use_case(
    artifact_repository: ArtifactRepositoryInterface = Depends(get_artifact_repository),
) -> ListArtifactsUseCase:
    """Injects dependencies into ListArtifactsUseCase."""
    return ListArtifactsUseCase(artifact_repository=artifact_repository)


def get_get_artifact_use_case(
    artifact_repository: ArtifactRepositoryInterface = Depends(get_artifact_repository),
) -> GetArtifactUseCase:
    """Injects dependencies into GetArtifactUseCase."""
    return GetArtifactUseCase(artifact_repository=artifact_repository)


def get_delete_artifact_use_case(
    artifact_repository: ArtifactRepositoryInterface = Depends(get_artifact_repository),
    storage_service: StorageServiceInterface = Depends(get_storage_service),
) -> DeleteArtifactUseCase:
    """Injects dependencies into DeleteArtifactUseCase."""
    return DeleteArtifactUseCase(
        artifact_repository=artifact_repository,
        storage_service=storage_service,
    )

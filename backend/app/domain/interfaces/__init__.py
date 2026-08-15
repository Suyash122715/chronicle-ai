"""Domain interfaces package."""

from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.background_job_service import BackgroundJobServiceInterface
from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.interfaces.prompt_repository import PromptRepositoryInterface
from app.domain.interfaces.storage_service import StorageServiceInterface
from app.domain.interfaces.text_extractor import TextExtractorInterface
from app.domain.interfaces.token_service import TokenServiceInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface

__all__ = [
    "ArtifactExtractorInterface",
    "ArtifactRepositoryInterface",
    "BackgroundJobServiceInterface",
    "DocumentClassifierInterface",
    "ExtractionRepositoryInterface",
    "LLMProviderInterface",
    "PromptRepositoryInterface",
    "StorageServiceInterface",
    "TextExtractorInterface",
    "TokenServiceInterface",
    "UserRepositoryInterface",
]

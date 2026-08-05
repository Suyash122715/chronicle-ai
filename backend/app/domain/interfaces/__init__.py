"""Domain interfaces package."""

from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.interfaces.prompt_repository import PromptRepositoryInterface

__all__ = [
    "ArtifactExtractorInterface",
    "LLMProviderInterface",
    "PromptRepositoryInterface",
]

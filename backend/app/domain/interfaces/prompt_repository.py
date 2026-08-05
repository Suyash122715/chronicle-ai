"""PromptRepository abstract domain interface."""

from abc import ABC, abstractmethod

from app.domain.value_objects.prompt_bundle import PromptBundle


class PromptRepositoryInterface(ABC):
    """Provider-independent domain interface for loading prompt markdown and output schemas.

    Strict Responsibilities:
    1. Load prompt markdown text
    2. Load JSON output schema
    3. Resolve prompt version

    Must NOT contain input validation, prompt rendering logic, or caching logic in the domain interface.
    """

    @abstractmethod
    def get_prompt_bundle(self, document_type: str, version: str | None = None) -> PromptBundle:
        """Loads raw prompt markdown, output JSON schema, and resolved version.

        Args:
            document_type: Document category name (e.g., 'resume', 'certificate').
            version: Optional explicit version identifier (e.g., 'v1'). Resolved to latest if None.

        Returns:
            A PromptBundle containing raw prompt text, schema dictionary, and prompt version string.
        """
        pass

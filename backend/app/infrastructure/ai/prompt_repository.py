"""FileSystemPromptRepository implementation."""

import json
import re
from pathlib import Path
from typing import Any

from app.domain.interfaces.prompt_repository import PromptRepositoryInterface
from app.domain.value_objects.prompt_bundle import PromptBundle


class FileSystemPromptRepository(PromptRepositoryInterface):
    """File-system based prompt repository implementation.

    Strict Responsibilities ONLY:
    - Load Markdown prompt files
    - Load JSON schema files
    - Resolve version strings

    No validation, rendering, or business logic.
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir is None:
            # Default to backend/prompts directory relative to repository root
            base_dir = Path(__file__).resolve().parents[3] / "prompts"
        self._base_dir = Path(base_dir)

    @property
    def base_dir(self) -> Path:
        """Returns the base directory path for prompts."""
        return self._base_dir

    def resolve_latest_version(self, document_type: str) -> str:
        """Resolves the latest prompt version string (e.g. 'v1') for a document type.

        Raises:
            FileNotFoundError: If the document type directory or no version files exist.
        """
        doc_dir = self._base_dir / document_type.strip().lower()
        if not doc_dir.exists() or not doc_dir.is_dir():
            raise FileNotFoundError(f"Prompt directory for document type '{document_type}' not found at '{doc_dir}'.")

        version_files = list(doc_dir.glob("v*.md"))
        if not version_files:
            raise FileNotFoundError(f"No prompt version files (v*.md) found in '{doc_dir}'.")

        def extract_version_key(path: Path) -> tuple[int, ...]:
            stem = path.stem  # e.g. "v1" or "v1.2"
            numbers = re.findall(r"\d+", stem)
            return tuple(map(int, numbers)) if numbers else (0,)

        latest_file = max(version_files, key=extract_version_key)
        return latest_file.stem

    def load_prompt(self, document_type: str, version: str | None = None) -> str:
        """Loads raw Markdown prompt text for a document type and version.

        Args:
            document_type: Category identifier string (e.g. 'resume').
            version: Explicit version (e.g. 'v1' or '1') or None to resolve latest.

        Returns:
            Raw Markdown prompt string.

        Raises:
            FileNotFoundError: If prompt file is missing.
        """
        doc_dir = self._base_dir / document_type.strip().lower()

        if version is None:
            resolved_version = self.resolve_latest_version(document_type)
        else:
            version_str = version.strip()
            resolved_version = version_str if version_str.startswith("v") else f"v{version_str}"

        prompt_file = doc_dir / f"{resolved_version}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found at '{prompt_file}'.")

        return prompt_file.read_text(encoding="utf-8")

    def load_schema(self, document_type: str) -> dict[str, Any]:
        """Loads JSON output schema dictionary for a document type.

        Args:
            document_type: Category identifier string (e.g. 'resume').

        Returns:
            Parsed JSON schema dictionary.

        Raises:
            FileNotFoundError: If schema.json is missing.
        """
        doc_dir = self._base_dir / document_type.strip().lower()
        schema_file = doc_dir / "schema.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found at '{schema_file}'.")

        raw_json = schema_file.read_text(encoding="utf-8")
        return json.loads(raw_json)

    def load_bundle(self, document_type: str, version: str | None = None) -> PromptBundle:
        """Loads a complete PromptBundle containing prompt text, schema, and resolved version.

        Args:
            document_type: Category identifier string (e.g. 'resume').
            version: Optional explicit version string or None.

        Returns:
            A PromptBundle value object.
        """
        prompt_text = self.load_prompt(document_type, version)
        schema = self.load_schema(document_type)
        if version is None:
            resolved_version = self.resolve_latest_version(document_type)
        else:
            v_str = version.strip()
            resolved_version = v_str if v_str.startswith("v") else f"v{v_str}"

        return PromptBundle(
            prompt_text=prompt_text,
            output_schema=schema,
            prompt_version=resolved_version,
        )

    def get_prompt_bundle(self, document_type: str, version: str | None = None) -> PromptBundle:
        """Domain interface contract implementation delegating to load_bundle."""
        return self.load_bundle(document_type, version)

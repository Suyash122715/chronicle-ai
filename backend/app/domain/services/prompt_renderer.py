"""PromptRenderer domain service implementation."""

import json
import re
from typing import Any

from app.domain.value_objects.prompt_bundle import PromptBundle
from app.domain.value_objects.rendered_prompt import RenderedPrompt


class PromptRenderer:
    """Renders prompt templates by replacing placeholders with supplied variables.

    Strict Responsibilities:
    - Accepts PromptBundle and template variables.
    - Replaces placeholders in double curly braces (e.g. {{document_text}}, {{output_schema}}, {{document_type}}).
    - Detects missing required template variables.
    - Produces an immutable RenderedPrompt value object.

    No filesystem access or prompt loading.
    """

    PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

    def render(
        self,
        bundle: PromptBundle,
        document_type: str,
        variables: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RenderedPrompt:
        """Renders prompt text from bundle by interpolating variables.

        Args:
            bundle: Target PromptBundle containing raw template text and schema.
            document_type: Document category name string (e.g. 'resume').
            variables: Optional dictionary mapping variable names to values.
            **kwargs: Additional keyword arguments for template variables.

        Returns:
            An immutable RenderedPrompt value object.

        Raises:
            ValueError: If a placeholder present in the prompt template is not supplied.
        """
        combined_vars: dict[str, Any] = {}
        if variables:
            combined_vars.update(variables)
        combined_vars.update(kwargs)

        # Supply default document_type and output_schema if not explicitly overridden
        if "document_type" not in combined_vars:
            combined_vars["document_type"] = document_type
        if "output_schema" not in combined_vars:
            combined_vars["output_schema"] = bundle.output_schema

        template_text = bundle.prompt_text
        found_placeholders = set(self.PLACEHOLDER_PATTERN.findall(template_text))

        # Check for missing variables required by template
        missing_vars = [var for var in found_placeholders if var not in combined_vars]
        if missing_vars:
            sorted_missing = sorted(missing_vars)
            raise ValueError(f"Missing required template variables: {', '.join(sorted_missing)}")

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            val = combined_vars[var_name]
            if isinstance(val, (dict, list)):
                return json.dumps(val, indent=2)
            return str(val)

        rendered_text = self.PLACEHOLDER_PATTERN.sub(replacer, template_text)

        return RenderedPrompt(
            rendered_text=rendered_text,
            schema=bundle.output_schema,
            prompt_version=bundle.prompt_version,
            document_type=document_type,
        )

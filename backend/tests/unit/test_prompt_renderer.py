"""Unit tests for PromptRenderer and RenderedPrompt."""

from dataclasses import FrozenInstanceError
import json
import pytest

from app.domain.services.prompt_renderer import PromptRenderer
from app.domain.value_objects.prompt_bundle import PromptBundle
from app.domain.value_objects.rendered_prompt import RenderedPrompt


def test_rendered_prompt_immutability_and_serialization() -> None:
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    rendered = RenderedPrompt(
        rendered_text="Rendered text content",
        schema=schema,
        prompt_version="v1",
        document_type="resume",
    )

    assert rendered.rendered_text == "Rendered text content"
    assert rendered.schema == schema
    assert rendered.prompt_version == "v1"
    assert rendered.document_type == "resume"

    with pytest.raises(FrozenInstanceError):
        rendered.prompt_version = "v2"  # type: ignore[misc]

    assert rendered.to_dict() == {
        "rendered_text": "Rendered text content",
        "schema": schema,
        "prompt_version": "v1",
        "document_type": "resume",
    }


def test_prompt_renderer_variable_replacement() -> None:
    renderer = PromptRenderer()
    bundle = PromptBundle(
        prompt_text="Type: {{document_type}}\nText:\n{{document_text}}\nSchema:\n{{output_schema}}",
        output_schema={"title": "TestSchema"},
        prompt_version="v1.2",
    )

    rendered = renderer.render(
        bundle=bundle,
        document_type="resume",
        document_text="John Doe Resume Content",
    )

    assert isinstance(rendered, RenderedPrompt)
    assert rendered.prompt_version == "v1.2"
    assert rendered.document_type == "resume"
    assert "Type: resume" in rendered.rendered_text
    assert "Text:\nJohn Doe Resume Content" in rendered.rendered_text
    assert json.dumps({"title": "TestSchema"}, indent=2) in rendered.rendered_text


def test_prompt_renderer_missing_variable_detection() -> None:
    renderer = PromptRenderer()
    bundle = PromptBundle(
        prompt_text="Hello {{name}}, welcome to {{city}}! Role: {{role}}",
        output_schema={},
        prompt_version="v1",
    )

    with pytest.raises(ValueError, match="Missing required template variables: city, name, role"):
        renderer.render(bundle=bundle, document_type="unknown")

    # Providing name, missing city and role
    with pytest.raises(ValueError, match="Missing required template variables: city, role"):
        renderer.render(bundle=bundle, document_type="unknown", name="Alice")


def test_prompt_renderer_repeated_placeholders() -> None:
    renderer = PromptRenderer()
    bundle = PromptBundle(
        prompt_text="Document: {{document_text}} | Repetition: {{document_text}} | Type: {{document_type}}",
        output_schema={},
        prompt_version="v1",
    )

    rendered = renderer.render(
        bundle=bundle,
        document_type="certificate",
        document_text="AWS Certified Developer",
    )

    assert rendered.rendered_text == "Document: AWS Certified Developer | Repetition: AWS Certified Developer | Type: certificate"


def test_prompt_renderer_custom_and_future_placeholders() -> None:
    renderer = PromptRenderer()
    bundle = PromptBundle(
        prompt_text="User: {{user_id}} | Task: {{task_name}} | Text: {{document_text}}",
        output_schema={},
        prompt_version="v2",
    )

    rendered = renderer.render(
        bundle=bundle,
        document_type="project",
        user_id="user_123",
        task_name="extraction_job",
        document_text="Project report text",
    )

    assert "User: user_123" in rendered.rendered_text
    assert "Task: extraction_job" in rendered.rendered_text
    assert "Text: Project report text" in rendered.rendered_text

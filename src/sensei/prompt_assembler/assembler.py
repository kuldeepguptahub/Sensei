"""
Prompt assembler for Sensei.

This module assembles complete prompts from templates and course data.
"""

from ..templates import load_template


class PromptAssemblyError(Exception):
    """Raised when prompt assembly fails."""
    pass


def _build_prompt(template_name: str, definition: str, state: str, context: str) -> str:
    """
    Internal helper to build a prompt from template and data.

    Args:
        template_name: Name of the template to load
        definition: Course definition content
        state: Course state content
        context: Course context content

    Returns:
        The assembled prompt as a string

    Raises:
        PromptAssemblyError: If template loading or assembly fails
    """
    try:
        # Load the template
        template = load_template(template_name)

        # Replace placeholders
        prompt = template.replace("{{definition}}", definition)
        prompt = prompt.replace("{{state}}", state)
        prompt = prompt.replace("{{context}}", context)

        # Verify all placeholders were replaced
        if "{{definition}}" in prompt or "{{state}}" in prompt or "{{context}}" in prompt:
            raise PromptAssemblyError(f"Template '{template_name}' contains unprocessed placeholders")

        return prompt

    except Exception as e:
        raise PromptAssemblyError(f"Failed to build prompt from template '{template_name}': {str(e)}")


def build_start_prompt(definition: str, state: str, context: str) -> str:
    """
    Build a start prompt from course data.

    Args:
        definition: Course definition content
        state: Course state content
        context: Course context content

    Returns:
        The assembled start prompt as a string
    """
    return _build_prompt("start", definition, state, context)


def build_resume_prompt(definition: str, state: str, context: str) -> str:
    """
    Build a resume prompt from course data.

    Args:
        definition: Course definition content
        state: Course state content
        context: Course context content

    Returns:
        The assembled resume prompt as a string
    """
    return _build_prompt("resume", definition, state, context)
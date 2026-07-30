"""
Template loader for Sensei.

This module provides a simple interface for loading template files.
"""

from pathlib import Path

# Base directory for templates
TEMPLATES_DIR = Path(__file__).parent / "prompts"


def load_template(name: str) -> str:
    """
    Load a template file by name.

    Args:
        name: The name of the template to load (without extension)

    Returns:
        The content of the template file as a string

    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    template_path = TEMPLATES_DIR / f"{name}.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template '{name}' not found at {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

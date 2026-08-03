"""
Agent runner for Sensei.

This module is responsible for:
- Loading agent instructions
- Registering skills
- Invoking the gateway
- Returning responses
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ..gateway.client import generate


def load_instructions() -> str:
    """
    Load the agent instructions from instructions.md.

    Returns:
        The content of the instructions file

    Raises:
        FileNotFoundError: If the instructions file doesn't exist
    """
    instructions_path = Path(__file__).parent / "instructions.md"
    return instructions_path.read_text(encoding='utf-8')


def run(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Run the Sensei agent with the given prompt and context.

    Args:
        prompt: The user prompt to process
        context: Optional context data for the agent

    Returns:
        The generated response from the agent
    """
    # Load agent instructions
    instructions = load_instructions()

    # Prepare the full prompt
    full_prompt = f"{instructions}\n\n---\n\nUser prompt: {prompt}"

    # Add context if provided
    if context:
        full_prompt += f"\n\nContext: {context}"

    # Invoke the gateway
    response = generate(full_prompt)

    return response
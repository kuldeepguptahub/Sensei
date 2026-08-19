"""
Gateway client for Sensei.

This is the public entry point for gateway operations.
"""
from typing import Dict, Any, Generator
from .provider import generate_with_provider, generate_with_provider_stream
from .retry import execute_with_retry


def generate(prompt: str) -> Dict[str, Any]:
    """
    Generate a response from the configured gateway.

    Args:
        prompt: The input prompt to generate a response for

    Returns:
        Dict with either:
          {"type": "text", "content": "..."} for text responses
          {"type": "tool_calls", "calls": [{"name": "...", "args": {...}}]} for tool calls

    Raises:
        GatewayError: For various gateway-related errors
    """
    def _generate_request():
        return generate_with_provider(prompt)

    # Execute with retry for transient failures
    return execute_with_retry(_generate_request)


def generate_stream(prompt: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generate a streaming response from the configured gateway.

    Yields chunks as they arrive:
      {"type": "text", "content": "..."} for text chunks
      {"type": "tool_calls", "calls": [...]} for tool calls (accumulated, single yield)

    Args:
        prompt: The input prompt to generate a response for

    Yields:
        Dict chunks with type "text" or "tool_calls"

    Raises:
        GatewayError: For various gateway-related errors
    """
    yield from generate_with_provider_stream(prompt)
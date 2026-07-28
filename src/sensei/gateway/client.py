"""
Gateway client for Sensei.

This is the public entry point for gateway operations.
"""
from .provider import generate_with_provider
from .retry import execute_with_retry


def generate(prompt: str) -> str:
    """
    Generate a response from the configured gateway.

    Args:
        prompt: The input prompt to generate a response for

    Returns:
        The generated response text

    Raises:
        GatewayError: For various gateway-related errors
    """
    def _generate_request():
        return generate_with_provider(prompt)

    # Execute with retry for transient failures
    return execute_with_retry(_generate_request)
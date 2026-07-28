"""
Mock provider for testing the gateway.
"""
import random
from typing import Dict, Any
from .config import load_config
from .exceptions import (
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayTimeoutError,
    GatewayRateLimitError,
    GatewayResponseError
)


def generate_with_provider(prompt: str) -> str:
    """
    Generate a response using the configured provider (mock implementation).

    Args:
        prompt: The input prompt to send to the provider

    Returns:
        The generated response text

    Raises:
        GatewayError: For various gateway-related errors
    """
    config = load_config()

    # Mock response for testing
    if "error" in prompt.lower():
        if "connection" in prompt.lower():
            raise GatewayConnectionError("Mock connection error")
        elif "auth" in prompt.lower():
            raise GatewayAuthenticationError("Mock authentication error")
        elif "timeout" in prompt.lower():
            raise GatewayTimeoutError("Mock timeout error")
        elif "rate" in prompt.lower():
            raise GatewayRateLimitError("Mock rate limit error")
        else:
            raise GatewayResponseError("Mock response error")

    # Simple mock response
    responses = [
        f"This is a mock response to: '{prompt}'. The configured model is {config.model_name}.",
        f"Mock AI response: I received your prompt '{prompt}'.",
        f"Test response for '{prompt}'. Using endpoint: {config.endpoint_url}"
    ]

    return random.choice(responses)
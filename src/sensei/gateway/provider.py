"""
Gateway provider for Sensei.

Handles real HTTP communication with LLM providers.
"""

import httpx
from typing import Dict, Any
from .config import load_config
from .providers import format_auth_header
from .exceptions import (
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayTimeoutError,
    GatewayRateLimitError,
    GatewayResponseError
)

# Hardcoded defaults for now
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TIMEOUT = 120.0


def generate_with_provider(prompt: str) -> str:
    """
    Generate a response using the configured provider.

    Args:
        prompt: The input prompt to send to the provider

    Returns:
        The generated response text

    Raises:
        GatewayError: For various gateway-related errors
    """
    config = load_config()

    # Build headers
    headers = format_auth_header(
        {"auth_header": config.auth_header, "auth_prefix": config.auth_prefix},
        config.api_key
    )

    # Build endpoint URL
    endpoint = f"{config.base_url}/chat/completions"

    # Build payload based on API type
    if config.api_type == "anthropic":
        payload = _build_anthropic_payload(prompt, config.model_id)
    else:
        payload = _build_openai_payload(prompt, config.model_id)

    # Make the request
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                endpoint,
                json=payload,
                headers=headers
            )
    except httpx.ConnectError as e:
        raise GatewayConnectionError(f"Failed to connect to {config.base_url}: {e}")
    except httpx.TimeoutException as e:
        raise GatewayConnectionError(f"Request timed out after {DEFAULT_TIMEOUT}s: {e}")
    except httpx.RequestError as e:
        raise GatewayConnectionError(f"Request failed: {e}")

    # Handle HTTP status codes
    if response.status_code == 401:
        raise GatewayAuthenticationError("Invalid API key. Please run 'sensei connect' to update.")
    elif response.status_code == 429:
        raise GatewayRateLimitError("Rate limit exceeded. Please wait and try again.")
    elif response.status_code >= 500:
        raise GatewayConnectionError(f"Server error ({response.status_code}): {response.text[:200]}")
    elif response.status_code != 200:
        raise GatewayResponseError(f"Unexpected response ({response.status_code}): {response.text[:200]}")

    # Parse response
    return _parse_response(response.json(), config.api_type)


def _build_openai_payload(prompt: str, model_id: str) -> Dict[str, Any]:
    """Build payload for OpenAI-compatible API."""
    return {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
    }


def _build_anthropic_payload(prompt: str, model_id: str) -> Dict[str, Any]:
    """Build payload for Anthropic API."""
    return {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    }


def _parse_response(data: Dict[str, Any], api_type: str) -> str:
    """Parse response from LLM provider."""
    try:
        if api_type == "anthropic":
            # Anthropic response format
            content = data.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            raise GatewayResponseError("Unexpected Anthropic response format")
        else:
            # OpenAI-compatible response format
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            raise GatewayResponseError("No choices in response")
    except (KeyError, IndexError, TypeError) as e:
        raise GatewayResponseError(f"Failed to parse response: {e}")

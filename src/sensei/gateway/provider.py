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
from ..logger import log_error

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
        msg = f"Failed to connect to {config.base_url}: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)
    except httpx.TimeoutException as e:
        msg = f"Request timed out after {DEFAULT_TIMEOUT}s: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)
    except httpx.RequestError as e:
        msg = f"Request failed: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)

    # Handle HTTP status codes
    if response.status_code == 401:
        msg = "Invalid API key. Please run 'sensei connect' to update your credentials."
        log_error(msg, f"Provider: {config.provider_name}")
        raise GatewayAuthenticationError(msg)
    elif response.status_code == 402:
        msg = (
            "Free credits exhausted. Purchase credits at your provider's billing page "
            "or subscribe for higher limits."
        )
        log_error(msg, f"Provider: {config.provider_name}")
        raise GatewayRateLimitError(msg)
    elif response.status_code == 429:
        msg = "Rate limit exceeded. Please wait a few minutes and try again."
        log_error(msg, f"Provider: {config.provider_name}")
        raise GatewayRateLimitError(msg)
    elif response.status_code >= 500:
        msg = (
            f"Server error from {config.provider_name} ({response.status_code}). "
            f"Please try again later or use a different provider."
        )
        log_error(msg)
        raise GatewayConnectionError(msg)
    elif response.status_code != 200:
        msg = (
            f"Unexpected response from {config.provider_name} ({response.status_code}). "
            f"Please check your configuration with 'sensei current'."
        )
        log_error(msg)
        raise GatewayResponseError(msg)

    # Parse response
    data = response.json()

    # Some providers return 200 with error in body
    if "error" in data:
        error_code = data["error"].get("code", 0)
        error_msg = data["error"].get("message", "Unknown error")
        if error_code == 429:
            log_error(f"Rate limit (in body): {error_msg}", f"Provider: {config.provider_name}")
            raise GatewayRateLimitError(f"Rate limit: {error_msg}")
        elif error_code == 402:
            log_error(f"Credits exhausted (in body): {error_msg}", f"Provider: {config.provider_name}")
            raise GatewayRateLimitError(f"Credits exhausted: {error_msg}")
        log_error(f"API error {error_code}: {error_msg}", f"Provider: {config.provider_name}")
        raise GatewayResponseError(f"API error ({error_code}): {error_msg}")

    return _parse_response(data, config.api_type)


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
                return choices[0].get("message", {}).get("content") or ""
            raise GatewayResponseError("No choices in response")
    except (KeyError, IndexError, TypeError) as e:
        raise GatewayResponseError(f"Failed to parse response: {e}")

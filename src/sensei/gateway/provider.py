"""
Gateway provider for Sensei.

Handles real HTTP communication with LLM providers.
"""

import json
import httpx
from typing import Dict, Any, Union, Generator
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


def generate_with_provider(prompt: str) -> Dict[str, Any]:
    """
    Generate a response using the configured provider.

    Args:
        prompt: The input prompt to send to the provider

    Returns:
        Dict with either:
          {"type": "text", "content": "..."} for text responses
          {"type": "tool_calls", "calls": [{"name": "...", "args": {...}}]} for tool calls

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


def generate_with_provider_stream(prompt: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generate a streaming response using the configured provider.

    Yields chunks as they arrive:
      {"type": "text", "content": "..."} for text chunks
      {"type": "tool_calls", "calls": [...]} for tool calls (accumulated, single yield)

    Args:
        prompt: The input prompt to send to the provider

    Yields:
        Dict chunks with type "text" or "tool_calls"

    Raises:
        GatewayError: For various gateway-related errors
    """
    config = load_config()

    headers = format_auth_header(
        {"auth_header": config.auth_header, "auth_prefix": config.auth_prefix},
        config.api_key
    )

    endpoint = f"{config.base_url}/chat/completions"

    if config.api_type == "anthropic":
        payload = _build_anthropic_payload(prompt, config.model_id)
    else:
        payload = _build_openai_payload(prompt, config.model_id)

    # Add stream flag for OpenAI-compatible APIs
    if config.api_type != "anthropic":
        payload["stream"] = True

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                # Handle HTTP errors before reading stream
                if response.status_code == 401:
                    msg = "Invalid API key. Please run 'sensei connect' to update your credentials."
                    log_error(msg, f"Provider: {config.provider_name}")
                    raise GatewayAuthenticationError(msg)
                elif response.status_code == 402:
                    msg = "Free credits exhausted. Purchase credits at your provider's billing page."
                    log_error(msg, f"Provider: {config.provider_name}")
                    raise GatewayRateLimitError(msg)
                elif response.status_code == 429:
                    msg = "Rate limit exceeded. Please wait a few minutes and try again."
                    log_error(msg, f"Provider: {config.provider_name}")
                    raise GatewayRateLimitError(msg)
                elif response.status_code >= 500:
                    msg = f"Server error from {config.provider_name} ({response.status_code})."
                    log_error(msg)
                    raise GatewayConnectionError(msg)
                elif response.status_code != 200:
                    msg = f"Unexpected response from {config.provider_name} ({response.status_code})."
                    log_error(msg)
                    raise GatewayResponseError(msg)

                # Parse SSE stream
                tool_call_accumulator = {}  # index -> {id, name, arguments_json}
                text_buffer = ""

                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    # Accumulate tool calls
                    if "tool_calls" in delta:
                        for tc_delta in delta["tool_calls"]:
                            idx = tc_delta.get("index", 0)
                            if idx not in tool_call_accumulator:
                                tool_call_accumulator[idx] = {
                                    "id": tc_delta.get("id", ""),
                                    "name": "",
                                    "arguments": ""
                                }
                            if "function" in tc_delta:
                                if "name" in tc_delta["function"]:
                                    tool_call_accumulator[idx]["name"] = tc_delta["function"]["name"]
                                if "arguments" in tc_delta["function"]:
                                    tool_call_accumulator[idx]["arguments"] += tc_delta["function"]["arguments"]

                    # Yield text content chunks
                    if "content" in delta and delta["content"]:
                        text_buffer += delta["content"]
                        yield {"type": "text", "content": delta["content"]}

                    # On finish, yield tool calls if any
                    if finish_reason == "tool_calls" and tool_call_accumulator:
                        calls = []
                        for idx in sorted(tool_call_accumulator.keys()):
                            tc = tool_call_accumulator[idx]
                            try:
                                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                            except json.JSONDecodeError:
                                args = {}
                            calls.append({"name": tc["name"], "args": args})
                        yield {"type": "tool_calls", "calls": calls}

    except httpx.ConnectError as e:
        msg = f"Failed to connect to {config.base_url}: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)
    except httpx.TimeoutException as e:
        msg = f"Request timed out: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)
    except httpx.RequestError as e:
        msg = f"Request failed: {e}"
        log_error(msg)
        raise GatewayConnectionError(msg)


def _build_openai_payload(prompt: str, model_id: str) -> Dict[str, Any]:
    """Build payload for OpenAI-compatible API with native tool support."""
    from ..agent.tools import get_openai_tool_definitions

    return {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "tools": get_openai_tool_definitions(),
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


def _parse_response(data: Dict[str, Any], api_type: str) -> Dict[str, Any]:
    """
    Parse response from LLM provider into structured format.

    Returns:
        {"type": "text", "content": "..."} for text responses
        {"type": "tool_calls", "calls": [{"name": "...", "args": {...}}]} for tool calls
    """
    try:
        if api_type == "anthropic":
            # Anthropic response format
            content = data.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
                return {"type": "text", "content": text}
            raise GatewayResponseError("Unexpected Anthropic response format")
        else:
            # OpenAI-compatible response format
            choices = data.get("choices", [])
            if not choices:
                raise GatewayResponseError("No choices in response")

            message = choices[0].get("message", {})
            if message is None:
                message = {}

            # Check for native tool calls
            tool_calls = message.get("tool_calls")
            if tool_calls:
                calls = []
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "")
                    raw_args = func.get("arguments", "{}")
                    # Arguments come as a JSON string, parse them
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = raw_args
                    calls.append({"name": name, "args": args})
                return {"type": "tool_calls", "calls": calls}

            # Text response
            content = message.get("content") or ""
            return {"type": "text", "content": content}

    except (KeyError, IndexError, TypeError) as e:
        raise GatewayResponseError(f"Failed to parse response: {e}")

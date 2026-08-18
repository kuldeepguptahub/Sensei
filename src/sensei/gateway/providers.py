"""
Provider registry for Sensei.

Defines supported LLM providers and their configurations.
"""

from typing import Dict, List, Optional


# Predefined provider configurations
PROVIDERS: Dict[str, Dict] = {
    "opencode-zen": {
        "name": "OpenCode Zen",
        "base_url": "https://opencode.ai/zen/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "gpt-5.5",
            "gpt-5.4-mini",
            "gpt-5.4-nano",
            "claude-sonnet-5",
            "claude-haiku-4-5",
            "deepseek-v4-pro",
            "deepseek-v4-flash",
        ]
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
        ]
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "auth_header": "x-api-key",
        "auth_prefix": "",
        "api_type": "anthropic",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250414",
            "claude-opus-4-20250514",
        ]
    },
    "ollama": {
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434/v1",
        "auth_header": None,
        "auth_prefix": "",
        "api_type": "openai",
        "models": []  # Dynamic, fetched from /v1/models
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "deepseek-chat",
            "deepseek-coder",
        ]
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]
    },
    "huggingface": {
        "name": "Hugging Face",
        "base_url": "https://router.huggingface.co/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        ]
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_type": "openai",
        "models": [
            "openai/gpt-oss-20b:free"
            "openrouter/free",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-haiku-4",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "meta-llama/llama-4-maverick",
            "deepseek/deepseek-chat-v3",
        ]
    },
}


def get_provider(name: str) -> Optional[Dict]:
    """
    Get a provider configuration by name.

    Args:
        name: Provider identifier (e.g., 'opencode-zen', 'openai')

    Returns:
        Provider config dict or None if not found
    """
    return PROVIDERS.get(name)


def list_providers() -> List[Dict]:
    """
    List all available providers.

    Returns:
        List of provider info dicts with 'id' added
    """
    return [{"id": k, **v} for k, v in PROVIDERS.items()]


def get_provider_names() -> List[str]:
    """
    Get list of provider identifiers.

    Returns:
        List of provider ID strings
    """
    return list(PROVIDERS.keys())


def format_auth_header(provider: Dict, api_key: str) -> Dict[str, str]:
    """
    Format authentication headers for a provider.

    Args:
        provider: Provider config dict
        api_key: API key string

    Returns:
        Dict of header name to header value
    """
    headers = {"Content-Type": "application/json"}

    if provider.get("auth_header"):
        prefix = provider.get("auth_prefix", "")
        if prefix:
            headers[provider["auth_header"]] = f"{prefix} {api_key}"
        else:
            headers[provider["auth_header"]] = api_key

    return headers

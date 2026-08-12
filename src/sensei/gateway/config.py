"""
Gateway configuration for Sensei.

Handles loading and saving provider/model configuration.
"""

import tomli
import tomli_w
from pathlib import Path
from typing import NamedTuple, Optional


class GatewayConfig(NamedTuple):
    """Gateway configuration data."""
    provider_name: str
    api_key: str
    model_id: str
    base_url: str
    auth_header: Optional[str]
    auth_prefix: str
    api_type: str


def get_config_path() -> Path:
    """Get the path to the config file.

    Returns:
        Absolute path to the config file

    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    # First try the current working directory
    config_path = Path("config.toml").absolute()

    if config_path.exists():
        return config_path

    # Try the project root
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.toml"

    if config_path.exists():
        return config_path

    raise FileNotFoundError("Config file not found. Please run 'sensei connect' first.")


def save_config(provider_name: str, api_key: str, model_id: str, base_url: str,
                auth_header: Optional[str], auth_prefix: str, api_type: str):
    """
    Save provider configuration to a TOML file.

    Args:
        provider_name: Provider identifier
        api_key: API key for the provider
        model_id: Selected model ID
        base_url: Provider base URL
        auth_header: Authentication header name (None for no auth)
        auth_prefix: Prefix for auth header value
        api_type: API type ('openai' or 'anthropic')
    """
    config_data = {
        "provider": {
            "name": provider_name,
            "base_url": base_url,
            "auth_header": auth_header,
            "auth_prefix": auth_prefix,
            "api_type": api_type,
        },
        "model": {
            "id": model_id,
        },
        "api_key": api_key,
    }

    with open("config.toml", "wb") as config_file:
        tomli_w.dump(config_data, config_file)


def load_config() -> GatewayConfig:
    """
    Load configuration from a TOML file.

    Returns:
        GatewayConfig: The loaded configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file is invalid or missing required fields
    """
    try:
        config_path = get_config_path()
        with open(config_path, "rb") as config_file:
            config_data = tomli.load(config_file)

        # New format: provider + model sections
        if "provider" in config_data:
            provider = config_data["provider"]
            model = config_data.get("model", {})
            api_key = config_data.get("api_key", "")

            return GatewayConfig(
                provider_name=provider.get("name", "unknown"),
                api_key=api_key,
                model_id=model.get("id", ""),
                base_url=provider.get("base_url", ""),
                auth_header=provider.get("auth_header"),
                auth_prefix=provider.get("auth_prefix", ""),
                api_type=provider.get("api_type", "openai"),
            )

        # Legacy format: flat structure
        if all(field in config_data for field in ["endpoint_url", "api_key", "model_name"]):
            return GatewayConfig(
                provider_name="custom",
                api_key=config_data["api_key"],
                model_id=config_data["model_name"],
                base_url=config_data["endpoint_url"].replace("/chat/completions", ""),
                auth_header="Authorization",
                auth_prefix="Bearer",
                api_type="openai",
            )

        # Legacy format with [default] section
        if "default" in config_data:
            default = config_data["default"]
            if all(field in default for field in ["endpoint_url", "api_key", "model_name"]):
                return GatewayConfig(
                    provider_name="custom",
                    api_key=default["api_key"],
                    model_id=default["model_name"],
                    base_url=default["endpoint_url"].replace("/chat/completions", ""),
                    auth_header="Authorization",
                    auth_prefix="Bearer",
                    api_type="openai",
                )

        raise ValueError("Invalid config format. Please run 'sensei connect' to set up.")

    except FileNotFoundError:
        raise FileNotFoundError("Config file not found. Please run 'sensei connect' first.")


def delete_config():
    """Delete the config file if it exists."""
    config_path = Path("config.toml")
    if config_path.exists():
        config_path.unlink()


def config_exists() -> bool:
    """Check if a config file exists."""
    try:
        get_config_path()
        return True
    except FileNotFoundError:
        return False

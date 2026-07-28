import tomli
import tomli_w
from pathlib import Path
from typing import NamedTuple


class GatewayConfig(NamedTuple):
    """Gateway configuration data."""
    endpoint_url: str
    api_key: str
    model_name: str


def save_config(endpoint_url: str, api_key: str, model_name: str):
    """
    Save configuration to a TOML file.
    """
    config_data = {
        "endpoint_url": endpoint_url,
        "api_key": api_key,
        "model_name": model_name
    }

    with open("config.toml", "wb") as config_file:
        tomli_w.dump(config_data, config_file)


def get_config_path():
    """Get the path to the config file.

    Returns:
        Path: Absolute path to the config file

    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    # First try the current working directory
    config_path = Path("config.toml").absolute()

    # If not found, try the project root
    if not config_path.exists():
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config.toml"

        if not config_path.exists():
            raise FileNotFoundError("Config file not found in current directory or project root")

    return config_path


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

        # Check if we have the default section
        if "default" not in config_data:
            # If no default section, assume the config is at the top level
            if all(field in config_data for field in ["endpoint_url", "api_key", "model_name"]):
                return GatewayConfig(
                    endpoint_url=config_data["endpoint_url"],
                    api_key=config_data["api_key"],
                    model_name=config_data["model_name"]
                )
            else:
                raise ValueError("Config file must have a [default] section or top-level configuration")

        default_config = config_data["default"]

        # Validate required fields
        required_fields = ["endpoint_url", "api_key", "model_name"]
        for field in required_fields:
            if field not in default_config:
                raise ValueError(f"Missing required field: {field}")

        return GatewayConfig(
            endpoint_url=default_config["endpoint_url"],
            api_key=default_config["api_key"],
            model_name=default_config["model_name"]
        )

    except FileNotFoundError:
        raise FileNotFoundError("Config file not found. Please run 'sensei setup' first.")
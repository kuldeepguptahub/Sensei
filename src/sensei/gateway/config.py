import tomli_w
from pathlib import Path

# function that writes toml file
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


# function that loads toml file
def load_config():
    """
    Load configuration from a TOML file.
    """
    with open("config.toml", "rb") as config_file:
        config_data = tomli_w.load(config_file)

    return config_data

# get config file path
def get_config_path():
    return Path("config.toml")
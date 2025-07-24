import os
import yaml
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# TODO: move to root of shared/ and have only config files under shared/configs/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHARED_CONFIG_PATH = Path(__file__).resolve().parents[0]

def _get_config_path(component_name: str) -> str | Path:
    env = os.getenv("APP_ENV", "dev")
    return PROJECT_ROOT.joinpath(
        'components', component_name, 'configs', f'{component_name}_{env}.yml'
    )

def component_config_loader(component_name: str) -> dict:
    """Load a YAML configuration file and convert it into a Python dictionary

    Fails immediately if the file is missing or contains invalid YAML

    Args:
        component_name (str): Name of component to load the configs for

    Returns:
        dict: A dictionary representing the loaded configuration

    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the file contains malformed or invalid YAML
    """

    try:
        path = _get_config_path(component_name)

        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        print(f"Failed to load YAML configuration: {e}", file=sys.stderr)
        sys.exit(1)

def global_config_loader() -> dict:
    """Load the global YAML configuration file and convert it into a Python dictionary

    Fails immediately if the file is missing or contains invalid YAML

    Returns:
        dict: A dictionary representing the loaded global configuration

    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the file contains malformed or invalid YAML
    """

    try:
        path = SHARED_CONFIG_PATH.joinpath("global_config.yml")

        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        print(f"Failed to load YAML configuration: {e}", file=sys.stderr)
        sys.exit(1)
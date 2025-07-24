import os
import yaml
import sys
from pathlib import Path
from dotenv import load_dotenv
from deepmerge import always_merger

load_dotenv()

# TODO: move to root of shared/ and have only config files under shared/configs/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHARED_CONFIG_PATH = Path(__file__).resolve().parents[0]

def _get_env_config_path(component_name: str) -> Path:
    env = os.getenv("APP_ENV", "dev")
    return PROJECT_ROOT.joinpath(
        'components', component_name, 'configs', f'{component_name}_{env}.yml'
    )


def _get_base_config_path(component_name: str) -> Path:
    return PROJECT_ROOT.joinpath(
        'components', component_name, 'configs', f'{component_name}_base_config.yml'
    )


def component_config_loader(component_name: str, use_base: bool = False) -> dict:
    """
    Load a YAML configuration file for a component. Optionally merges with a base config

    Args:
        component_name (str): Name of the component
        use_base (bool): Whether to merge with a component base_config.yml

    Returns:
        dict: Loaded and possibly merged configuration
    """

    try:
        env_config_path  = _get_env_config_path(component_name)
        base_config_path = _get_base_config_path(component_name)

        if use_base and base_config_path.exists():
            with open(base_config_path, 'r') as base_file, open(env_config_path, 'r') as env_file:
                base_cfg = yaml.safe_load(base_file) or {}
                env_cfg = yaml.safe_load(env_file) or {}
                return always_merger.merge(base_cfg, env_cfg)
        else:
            with open(env_config_path, 'r') as env_file:
                return yaml.safe_load(env_file) or {}
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
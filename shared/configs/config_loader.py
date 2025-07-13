import yaml
import sys
from pathlib import Path


def config_loader(path: str | Path) -> dict:
    """Load a YAML configuration file and convert it into a Python dictionary

    Fails immediately if the file is missing or contains invalid YAML

    Args:
        path (str | Path): Path to the YAML configuration file

    Returns:
        dict: A dictionary representing the loaded configuration

    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the file contains malformed or invalid YAML
    """
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        print(f"Failed to load YAML configuration: {e}", file=sys.stderr)
        sys.exit(1)
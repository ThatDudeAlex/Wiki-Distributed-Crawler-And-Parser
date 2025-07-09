import yaml
from pathlib import Path
from shared.configs.dotdict import DotDict


def load_config(path: str | Path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return DotDict(data)

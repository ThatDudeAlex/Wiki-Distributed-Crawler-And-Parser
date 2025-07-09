from shared.configs.load_config import Path, load_config

PROJECT_ROOT = Path(__file__).resolve().parents[3]

config_path = PROJECT_ROOT.joinpath(
    'components', 'scheduler', 'configs', 'scheduler_config.yml'
)

configs = load_config(config_path)

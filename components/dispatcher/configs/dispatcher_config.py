from dotenv import load_dotenv
from components.dispatcher.types.config_types import DispatcherConfig
from shared.configs.load_config import Path, load_config

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

config_path = PROJECT_ROOT.joinpath(
    'components', 'dispatcher', 'configs', 'config.yml'
)

configs: DispatcherConfig = load_config(config_path)

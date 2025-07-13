from dotenv import load_dotenv
from shared.configs.load_config import Path, load_config

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

config_path = PROJECT_ROOT.joinpath(
    'components', 'rescheduler', 'configs', 'config.yml'
)

configs = load_config(config_path)

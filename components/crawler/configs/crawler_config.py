import os
from dotenv import load_dotenv
from components.crawler.types.config_types import CrawlerConfig
from shared.configs.load_config import Path, load_config

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

config_path = PROJECT_ROOT.joinpath(
    'components', 'crawler', 'configs', 'crawler_config.yml'
)

configs: CrawlerConfig = load_config(config_path)
configs.storage_path = os.getenv('DL_HTML_PATH')

# For local use/test
# configs: CrawlerConfig = load_config(<Full Absolute Path To YML>)
# configs.storage_path = os.getenv('DL_HTML_PATH')

import os
from dotenv import load_dotenv
from components.crawler.types.config_types import CrawlerConfig
from shared.configs.load_config import load_config

load_dotenv()
configs: CrawlerConfig = load_config(
    "/app/components/crawler/configs/crawler_config.yml"
)
configs.storage_path = os.getenv('DL_HTML_PATH')

# For local use/test
# configs: CrawlerConfig = load_config(<Full Absolute Path To YML>)
# configs.storage_path = os.getenv('DL_HTML_PATH')

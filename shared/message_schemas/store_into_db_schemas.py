from pydantic import BaseModel, HttpUrl, FilePath
from typing import Optional
from database.db_models.models import CrawlStatus
from components.crawler.configs.app_configs import MAX_DEPTH


class SavePageTask(BaseModel):
    url: HttpUrl
    url_hash: Optional[str]
    crawl_time: str
    crawl_status: CrawlStatus
    status_code: Optional[int]
    compressed_path: Optional[FilePath]


class SaveParsedContent(BaseModel):
    page_url: HttpUrl
    title: str
    summary: str
    content: str
    parse_time: str
    categories: Optional[list[str]]

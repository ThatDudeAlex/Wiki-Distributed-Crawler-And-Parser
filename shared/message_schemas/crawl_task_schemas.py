from pydantic import BaseModel, Field, HttpUrl, FilePath
from typing import Optional
from database.db_models.models import CrawlStatus
from components.crawler.configs.app_configs import MAX_DEPTH


class CrawlTask(BaseModel):
    url: HttpUrl
    depth: Optional[int] = Field(default=0, ge=0, le=MAX_DEPTH)


class FailedCrawlTask(BaseModel):
    url: HttpUrl
    crawl_status: CrawlStatus
    status_code: Optional[int]
    error_message: Optional[str]

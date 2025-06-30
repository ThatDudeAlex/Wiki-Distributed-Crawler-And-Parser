from dataclasses import dataclass
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from database.db_models.models import CrawlStatus
from components.crawler.configs.app_configs import MAX_DEPTH


class CrawlTaskSchema(BaseModel):
    url: HttpUrl
    depth: Optional[int] = Field(default=0, ge=0, le=MAX_DEPTH)


class FailedCrawlTaskSchema(BaseModel):
    url: HttpUrl
    crawl_status: CrawlStatus
    status_code: Optional[int]
    error_message: Optional[str]


@dataclass
class CrawlTask:
    url: str
    depth: Optional[int] = 0


@dataclass
class FailedCrawlTask:
    url: str
    crawl_status: CrawlStatus
    status_code: Optional[int] = None
    error_message: Optional[str] = None

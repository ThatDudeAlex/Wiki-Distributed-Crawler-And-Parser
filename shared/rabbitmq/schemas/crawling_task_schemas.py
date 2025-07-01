from datetime import datetime
from typing import Annotated, Literal, Union
from pydantic import Field
from pydantic import BaseModel, HttpUrl
from shared.rabbitmq.enums.crawl_status import CrawlStatus


# === Crawling Task (Scheduler → Crawler) ===

class CrawlTask(BaseModel):
    url: HttpUrl
    scheduled_at: datetime
    depth: int = 0
    retry_count: int = 0


# === Crawl Report (Crawler → Scheduler) ===

class CrawlReportBase(BaseModel):
    url: HttpUrl
    status: CrawlStatus
    fetched_at: datetime


class SuccessCrawlReport(CrawlReportBase):
    status: Literal[CrawlStatus.CRAWLED_SUCCESS]
    http_status: int
    url_hash: str
    content_hash: str
    compressed_filepath: str


class FailedCrawlReport(CrawlReportBase):
    status: Literal[CrawlStatus.CRAWL_FAILED]
    error: str
    retryable: bool


CrawlReport = Annotated[
    Union[SuccessCrawlReport, FailedCrawlReport],
    Field(discriminator="status")
]


# === Crawl Metadata Message (Scheduler → DB Writer) ===

class CrawlMetadataMessage(BaseModel):
    url: HttpUrl
    status: CrawlStatus
    http_status:         int | None = None   # null if failed
    url_hash:            str | None = None   # null if failed
    content_hash:        str | None = None   # null if failed
    compressed_filepath: str | None = None   # null if failed
    fetched_at: datetime
    error: str | None = None
    retryable: bool | None = None

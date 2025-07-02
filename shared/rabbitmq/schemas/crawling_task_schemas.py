from datetime import datetime
from typing import Annotated, Literal, Optional, Union
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
    status: CrawlStatus
    fetched_at: datetime
    url: HttpUrl


class SuccessCrawlReport(CrawlReportBase):
    status: Literal[CrawlStatus.CRAWLED_SUCCESS]
    http_status_code: int
    url_hash: str
    html_content_hash: str
    compressed_filepath: str


class FailedCrawlReport(CrawlReportBase):
    status: Literal[CrawlStatus.CRAWL_FAILED, CrawlStatus.SKIPPED]
    error_type: Optional[str] = None     # None when skipped due to robots.txt
    error_message: Optional[str] = None  # None when skipped due to robots.txt
    # retryable: Optional[bool] = None


CrawlReport = Annotated[
    Union[SuccessCrawlReport, FailedCrawlReport],
    Field(discriminator="status")
]


# === Crawl Metadata Message (Scheduler → DB Writer) ===

class CrawlMetadataMessage(BaseModel):
    status: CrawlStatus
    fetched_at: datetime
    url: HttpUrl
    http_status_code: Optional[int] = None      # None if failed
    url_hash: Optional[str] = None              # None if failed
    html_content_hash: Optional[str] = None     # None if failed
    compressed_filepath: Optional[str] = None   # None if failed
    error_type: Optional[str] = None            # None if success
    error_message: Optional[str] = None         # None if success
    # retryable: Optional[bool] = None


class FetchPageMetadata(BaseModel):
    url: HttpUrl

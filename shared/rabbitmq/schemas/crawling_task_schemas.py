from datetime import datetime
from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from pydantic import BaseModel, HttpUrl
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.types import PageMetadata


# === Crawling Task (Scheduler → Crawler) ===

# TODO: Pydantic - create a dataclass to then easily convert this
class CrawlTask(BaseModel):
    url: HttpUrl
    scheduled_at: datetime
    depth: int = 0
    retry_count: int = 0


# === Crawl Metadata Message (Crawler → DB Writer) ===

# TODO: Pydantic - Make a BaseClass so that all models have to_dataclass()
class PageMetadataMessage(BaseModel):
    status: CrawlStatus
    fetched_at: datetime
    url: HttpUrl
    http_status_code: Optional[int] = None      # None if failed
    url_hash: Optional[str] = None              # None if failed
    html_content_hash: Optional[str] = None     # None if failed
    compressed_filepath: Optional[str] = None   # None if failed
    error_type: Optional[str] = None            # None if success
    error_message: Optional[str] = None         # None if success

    def to_dataclass(self) -> PageMetadata:
        return PageMetadata(
            status=self.status,
            fetched_at=self.fetched_at,
            url=str(self.url),  # Convert HttpUrl to string
            http_status_code=self.http_status_code,
            url_hash=self.url_hash,
            html_content_hash=self.html_content_hash,
            compressed_filepath=self.compressed_filepath,
            error_type=self.error_type,
            error_message=self.error_message
        )


# TODO: Remove if not needed
class FetchPageMetadata(BaseModel):
    url: HttpUrl

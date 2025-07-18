from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse
from shared.rabbitmq.enums.crawl_status import CrawlStatus


class SavePageMetadataTask(BaseModel):
    status: CrawlStatus
    fetched_at: str
    url: str
    http_status_code: Optional[int] = None      # None if failed
    url_hash: Optional[str] = None              # None if failed
    html_content_hash: Optional[str] = None     # None if failed
    compressed_filepath: Optional[str] = None   # None if failed
    next_crawl: Optional[str] = None            # None if failed
    error_type: Optional[str] = None            # None if success
    error_message: Optional[str] = None         # None if success

    @field_validator("url")
    @classmethod
    def must_be_valid_url(cls, url: str) -> str:
        result = urlparse(url)
        if not (result.scheme and result.netloc):
            raise ValueError("Invalid URL format")
        return url
    
    @field_validator("fetched_at")
    @classmethod
    def validate_iso_datetime(cls, fetched_at: str) -> str:
        try:
            datetime.fromisoformat(fetched_at)
        except ValueError:
            raise ValueError("fetched_at must be a valid ISO 8601 datetime string")
        return fetched_at
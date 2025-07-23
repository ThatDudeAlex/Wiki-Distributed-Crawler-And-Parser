from pydantic import BaseModel, field_validator
from datetime import datetime
from urllib.parse import urlparse

# TODO: Add Optional 'html_content_hash' field. If the field is present we then know the
#       crawl task is for recrawling a previous page, and the hash can be used to determine
#       if the page has changed and requires a redownload of the html_content
class CrawlTask(BaseModel):
    url: str
    scheduled_at: str # ISO 8601 string (could be useful to help debugging)
    depth: int = 0

    @field_validator("url")
    @classmethod
    def must_be_valid_url(cls, url: str) -> str:
        result = urlparse(url)
        if not (result.scheme and result.netloc):
            raise ValueError("Invalid URL format")
        return url
    
    @field_validator("depth")
    @classmethod
    def validate_depth(cls, depth: int) -> int:
        if depth < 0:
            raise ValueError("Depth must be a non-negative integer")
        return depth
    
    @field_validator("scheduled_at")
    @classmethod
    def validate_iso_datetime(cls, scheduled_at: str) -> str:
        try:
            datetime.fromisoformat(scheduled_at)
        except ValueError:
            raise ValueError("scheduled_at must be a valid ISO 8601 datetime string")
        return scheduled_at
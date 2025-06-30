from pydantic import BaseModel
from typing import Literal, Optional, TypedDict
from database.db_models.models import CrawlStatus

CrawlerErrorType = Literal[
    "HTTPError",
    "Timeout",
    "ConnectionError",
    "TooManyRedirects",
    "SSLError",
    "RequestException"
]


class ResponseData(BaseModel):
    status_code: int
    headers: Optional[dict]
    text: Optional[str]


class CrawlError(TypedDict):
    type: CrawlerErrorType
    message: str


class CrawlerResponse(BaseModel):
    success: bool
    url: str
    crawl_status: CrawlStatus
    data: Optional[ResponseData]
    error: Optional[CrawlError]

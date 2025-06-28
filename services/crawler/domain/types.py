# TODO: cleanup these comments when done
# pydantic throws ValidationError when failed
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
    headers: dict
    text: str


class CrawlError(TypedDict):
    type: CrawlerErrorType
    message: str


class CrawlerResponse(BaseModel):
    success: bool
    crawl_status: CrawlStatus
    data: Optional[ResponseData]  # the actual request response
    error: Optional[CrawlError]

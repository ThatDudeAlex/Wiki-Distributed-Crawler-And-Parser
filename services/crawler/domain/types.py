# TODO: cleanup these comments when done
# pydantic throws ValidationError when failed
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, FilePath
from typing import Literal, Optional, TypedDict
from database.db_models.models import CrawlStatus
from services.crawler.config import MAX_DEPTH

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
    url: HttpUrl
    crawl_status: CrawlStatus
    data: Optional[ResponseData]
    error: Optional[CrawlError]


class CrawlTask(BaseModel):
    url: HttpUrl
    depth: Optional[int] = Field(default=0, ge=0, le=MAX_DEPTH)


class FailedCrawlTask(BaseModel):
    url: HttpUrl
    crawl_status: CrawlStatus
    status_code: Optional[int]
    error_message: Optional[str]


class SavePageTask(BaseModel):
    url: HttpUrl
    url_hash: str
    crawl_status: CrawlStatus
    compressed_path: FilePath
    crawl_time: str
    status_code: int


class ParseDonwloadedPageTask(BaseModel):
    url: HttpUrl
    compressed_path: FilePath

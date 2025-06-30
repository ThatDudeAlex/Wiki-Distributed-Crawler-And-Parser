from dataclasses import dataclass
from pydantic import BaseModel
from typing import Dict, Literal, Optional, TypedDict
from database.db_models.models import CrawlStatus

CrawlerErrorType = Literal[
    "HTTPError",
    "Timeout",
    "ConnectionError",
    "TooManyRedirects",
    "SSLError",
    "RequestException"
]


@dataclass
class ResponseData:
    status_code: int
    headers: Optional[Dict] = None
    text: Optional[str] = None


@dataclass
class CrawlError:
    type: CrawlerErrorType
    message: str


@dataclass
class CrawlerResponse:
    success: bool
    url: str
    crawl_status: CrawlStatus
    data: Optional[ResponseData] = None
    error: Optional[CrawlError] = None

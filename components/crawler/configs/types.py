from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
from shared.rabbitmq.enums.crawl_status import CrawlStatus

# TODO: refactor the @dataclasses since the current
#       setup is not so great


class CrawlerErrorType(str, Enum):
    HTTP_ERROR = "HTTPError"
    TIMEOUT = "Timeout"
    CONNECTION_ERROR = "ConnectionError"
    TOO_MANY_REDIRECTS = "TooManyRedirects"
    SSL_ERROR = "SSLError"
    REQUEST_EXCEPTION = "RequestException"


@dataclass
class CrawlerResponse:
    success: bool
    url: str
    crawl_status: Optional[CrawlStatus]
    status_code: Optional[int] = None
    headers: Optional[Dict] = None
    text: Optional[str] = None
    error_type: Optional[CrawlerErrorType] = None
    error_message: Optional[str] = None

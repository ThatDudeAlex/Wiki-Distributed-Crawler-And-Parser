import requests
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
from shared.rabbitmq.enums.crawl_status import CrawlStatus


class CrawlerErrorType(str, Enum):
    """
    Represents specific error types that may occur during a crawl operation.

    Values:
        - HTTP_ERROR: Server returned 4xx or 5xx status
        - TIMEOUT: Request timed out
        - CONNECTION_ERROR: Failed to establish a connection
        - TOO_MANY_REDIRECTS: Exceeded allowed redirects
        - SSL_ERROR: SSL certificate validation failed
        - REQUEST_EXCEPTION: Generic or uncategorized request error
    """
    HTTP_ERROR = "HTTPError"
    TIMEOUT = "Timeout"
    CONNECTION_ERROR = "ConnectionError"
    TOO_MANY_REDIRECTS = "TooManyRedirects"
    SSL_ERROR = "SSLError"
    REQUEST_EXCEPTION = "RequestException"

    __EXCEPTION_MAP = {
        requests.exceptions.HTTPError: HTTP_ERROR,
        requests.exceptions.Timeout: TIMEOUT,
        requests.exceptions.ConnectionError: CONNECTION_ERROR,
        requests.exceptions.TooManyRedirects: TOO_MANY_REDIRECTS,
        requests.exceptions.SSLError: SSL_ERROR,
    }

    @classmethod
    def from_exception(cls, exc: requests.RequestException) -> "CrawlerErrorType":
        exc_type = type(exc)
        if exc_type in cls.__EXCEPTION_MAP:
            return cls.__EXCEPTION_MAP[exc_type]
        return cls.REQUEST_EXCEPTION


# Is a dataclass because is never coming from external, untrusted data so I don't need 
# Pydantic validation
@dataclass
class FetchResponse:
    """
    Result object for a crawl operation.

    Attributes:
        success (bool): Whether the crawl was successful
        url (str): URL that was crawled
        crawl_status (Optional[CrawlStatus]): Crawl status (SUCCESS or FAILED)
        status_code (Optional[int]): HTTP response code
        headers (Optional[Dict[str, str]]): Response headers
        text (Optional[str]): Page content (HTML)
        error_type (Optional[CrawlerErrorType]): Crawler-specific error category
        error_message (Optional[str]): Raw error message if failed
    """
    success: bool
    url: str
    crawl_status: Optional[CrawlStatus]
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    text: Optional[str] = None
    error_type: Optional[CrawlerErrorType] = None
    error_message: Optional[str] = None

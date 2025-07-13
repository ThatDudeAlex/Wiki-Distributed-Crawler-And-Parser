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

    @classmethod
    def from_exception(cls, exc: requests.RequestException) -> "CrawlerErrorType":
        exc_type = type(exc)
        if exc_type in cls._EXCEPTION_MAP:
            return cls._EXCEPTION_MAP[exc_type]
        return cls.REQUEST_EXCEPTION

    _EXCEPTION_MAP = {
        requests.exceptions.HTTPError: HTTP_ERROR,
        requests.exceptions.Timeout: TIMEOUT,
        requests.exceptions.ConnectionError: CONNECTION_ERROR,
        requests.exceptions.TooManyRedirects: TOO_MANY_REDIRECTS,
        requests.exceptions.SSLError: SSL_ERROR,
    }


@dataclass
class FetchResponse:
    """
    Represents the result of a page crawl operation

    Attributes:
        success (bool): Whether the crawl was successful
        url (str): The URL that was crawled
        crawl_status (Optional[CrawlStatus]): The result status of the crawl
        status_code (Optional[int]): The HTTP response code, if any
        headers (Optional[Dict]): The HTTP headers from the response
        text (Optional[str]): The raw HTML/text of the response
        error_type (Optional[CrawlerErrorType]): The type of error if failed
        error_message (Optional[str]): A descriptive error message
    """
    success: bool
    url: str
    crawl_status: Optional[CrawlStatus]
    status_code: Optional[int] = None
    headers: Optional[Dict] = None
    text: Optional[str] = None
    error_type: Optional[CrawlerErrorType] = None
    error_message: Optional[str] = None

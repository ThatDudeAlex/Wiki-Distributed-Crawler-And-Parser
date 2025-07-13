import logging
import requests
from ratelimit import limits, sleep_and_retry
from components.crawler.types.crawler_types import FetchResponse, CrawlerErrorType
from shared.rabbitmq.enums.crawl_status import CrawlStatus

class HttpFetcher:
    """
    A rate-limited HTTP fetcher that wraps requests to enforce API call limits

    Args:
        configs (dict): Configuration dictionary with rate limit and request settings
        logger (logging.Logger): Logger instance for reporting fetch status and errors

    Attributes:
        max_requests (int): Maximum allowed requests per period
        period (int): Time window (in seconds) for the rate limit
        headers (dict): Default headers to include in requests
        timeout (int): Timeout duration for HTTP requests
    """

    def __init__(self, configs: dict, logger: logging.Logger):
        self._logger = logger
        self.max_requests = configs['rate_limit']['max_requests_per_period']
        self.period  = configs['rate_limit']['period_in_seconds']
        self.headers = configs['requests']['headers']
        self.timeout = configs['requests']['timeout_in_seconds']


    def _rate_limited_fetch(self, url: str) -> requests.Response:
        @sleep_and_retry
        @limits(calls=self.max_requests, period=self.period)
        def inner():
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response
        
        return inner()


    def crawl_url(self, url: str) -> FetchResponse:
        """
        Perform a crawl of the specified URL, respecting rate limits, and returns a FetchResponse

        Args:
            url (str): url for the page to crawl

        Returns:
            FetchResponse: Dataclass with the following fields:
                - success (bool): Whether the request succeeded
                - url (str): The original URL
                - crawl_status (CrawlStatus, optional): Status of the crawl
                - status_code (int, optional): HTTP status code
                - headers (dict, optional): Response headers
                - text (str, optional): Page content
                - error_type (CrawlerErrorType, optional): Enum indicating error type
                - error_message (str, optional): Error details if failed

        Raises:
            requests.RequestException: If an unexpected error occurred
        """
        try:
            response = self._rate_limited_fetch(url)

            self._logger.info("Fetched URL successfully: %s (status: %s)", url, response.status_code)

            return FetchResponse(
                success=True,
                url=url,
                crawl_status=CrawlStatus.SUCCESS,
                status_code=response.status_code,
                headers=dict(response.headers),
                text=response.text
            )

        except requests.RequestException as e:
            error_type = CrawlerErrorType.from_exception(e)
            
            self._logger.error(
                "Failed to fetch URL: %s | Error Type: %s | Message: %s",
                url,
                error_type.value,
                str(e)
            )

            return FetchResponse(
                success=False,
                url=url,
                crawl_status=CrawlStatus.FAILED,
                error_type=error_type,
                error_message=str(e)
            )

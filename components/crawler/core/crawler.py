import logging
import requests
from ratelimit import limits, sleep_and_retry

from components.crawler.types.crawler_types import FetchResponse
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.config import BASE_HEADERS


@sleep_and_retry
@limits(calls=1, period=1)
def _fetch(url: str) -> requests.Response:
    """
    Make a GET request to the given URL with default headers
    """
    response = requests.get(url, headers=BASE_HEADERS, timeout=10)
    response.raise_for_status()
    return response


def crawl(url: str, logger: logging.Logger) -> FetchResponse:
    """
    Perform a crawl of the specified URL, respecting robots.txt, and return a FetchResponse
    """
    try:

        response = _fetch(url)
        logger.info('Successfully Fetched URL: %s', url)

        return FetchResponse(
            True, url, CrawlStatus.SUCCESS,
            response.status_code, dict(response.headers), response.text
        )

    except requests.HTTPError as e:
        logger.error("HTTPError in '%s' - StatusCode: %s - %s", url,
                     e.response.status_code if e.response else "N/A", str(e))
        return FetchResponse(
            success=False, url=url, crawl_status=CrawlStatus.FAILED,
            error_type=type(e).__name__, error_message=str(e)
        )

    except requests.RequestException as e:
        logger.error(f"Unexpected error in '{url}' - {e}")
        return FetchResponse(
            success=False, url=url, crawl_status=CrawlStatus.FAILED,
            error_type=type(e).__name__, error_message=str(e)
        )

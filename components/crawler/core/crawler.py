import logging
from typing import Optional
import requests
import urllib.robotparser

from components.crawler.configs.types import FetchResponse
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from components.crawler.configs.app_configs import ROBOTS_TXT, BASE_HEADERS


def _robot_blocks_crawling(url: str, logger: logging.Logger) -> bool:
    """
    Returns True if robots.txt blocks crawling the URL; otherwise, False.
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_TXT)
    rp.read()

    if rp.can_fetch(BASE_HEADERS['user-agent'], url):
        return False
    else:
        logger.warning(f"robots.txt blocked crawling: {url}")
        return True


def _fetch(url: str) -> requests.Response:
    """
    Make a GET request to the given URL with default headers.
    """
    response = requests.get(url, headers=BASE_HEADERS, timeout=10)
    response.raise_for_status()
    return response


def crawl(url: str, logger: logging.Logger) -> FetchResponse:
    """
    Perform a crawl of the specified URL, respecting robots.txt, and return a CrawlerResponse.
    """
    try:
        logger.info('Verifying that robots.txt allows crawling URL: %s', url)

        if _robot_blocks_crawling(url, logger):
            return FetchResponse(False, url, CrawlStatus.SKIPPED)

        response = _fetch(url)
        logger.info('Successfully Fetched URL: %s', url)

        return FetchResponse(
            True, url, CrawlStatus.CRAWLED_SUCCESS,
            response.status_code, dict(response.headers), response.text
        )

    except requests.HTTPError as e:
        logger.error("HTTPError in '%s' - StatusCode: %s - %s", url,
                     e.response.status_code if e.response else "N/A", str(e))
        return FetchResponse(success=False, url=url, crawl_status=CrawlStatus.CRAWL_FAILED, error=e)

    except requests.RequestException as e:
        logger.error(f"RequestException in '{url}' - {e}")
        return FetchResponse(success=False, url=url, crawl_status=CrawlStatus.SKIPPED, error=e)

import logging
from typing import Optional, Union
import requests
import urllib.robotparser

from components.crawler.configs.types import CrawlerResponse, ResponseData
from database.db_models.models import CrawlStatus
from components.crawler.configs.app_configs import ROBOTS_TXT, BASE_HEADERS


def _generate_crawler_response(
    success: bool,
    url: str,
    crawl_status: CrawlStatus,
    data: Optional[Union[ResponseData, dict]] = None,
    error: Optional[Exception] = None
) -> CrawlerResponse:
    """
    Build a CrawlerResponse, extracting error details and response data if needed.
    """
    if not success and error:
        # If the exception has a response (e.g., HTTPError), extract its data
        response = getattr(error, "response", None)
        if response:
            data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text,
            }

        err = {
            'type': error.__class__.__name__,
            'message': str(error),
        }
    else:
        err = None

    return CrawlerResponse(
        success=success,
        url=url,
        crawl_status=crawl_status,
        data=data,
        error=err
    )


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


def crawl(url: str, logger: logging.Logger) -> CrawlerResponse:
    """
    Perform a crawl of the specified URL, respecting robots.txt, and return a CrawlerResponse.
    """
    try:
        logger.info('Verifying that robots.txt allows crawling URL: %s', url)

        if _robot_blocks_crawling(url, logger):
            return _generate_crawler_response(False, url, CrawlStatus.SKIPPED)

        response = _fetch(url)
        logger.info('Successfully Fetched URL: %s', url)

        return _generate_crawler_response(
            True,
            url,
            CrawlStatus.CRAWLED_SUCCESS,
            {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text
            }
        )

    except requests.HTTPError as e:
        logger.error("HTTPError in '%s' - StatusCode: %s - %s", url,
                     e.response.status_code if e.response else "N/A", str(e))
        return _generate_crawler_response(False, url, CrawlStatus.CRAWL_FAILED, error=e)

    except requests.RequestException as e:
        logger.error(f"RequestException in '{url}' - {e}")
        return _generate_crawler_response(False, url, CrawlStatus.CRAWL_FAILED, error=e)

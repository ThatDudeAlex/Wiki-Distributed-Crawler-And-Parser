import logging
import requests
import urllib.robotparser

from components.crawler.configs.types import CrawlerResponse, ResponseData
from database.db_models.models import CrawlStatus
from components.crawler.configs.app_configs import ROBOTS_TXT, BASE_HEADERS


def _generate_crawler_response(
    success: bool,
    url: str,
    crawl_status: CrawlStatus,
    data: ResponseData,
    error: dict
) -> CrawlerResponse:
    return CrawlerResponse(
        success=success,
        url=url,
        crawl_status=crawl_status,
        data=data,
        error=error
    )


def _robot_allows_crawling(url: str, logger: logging.Logger) -> bool:
    """
    Returns ``True`` if robot.txt allows crawling the ``URL`` else
    returns ``False``
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_TXT)
    rp.read()

    if not rp.can_fetch(BASE_HEADERS['user-agent'], url):
        logger.warning(f"robots.txt blocked crawling: {url}")
        return False
    return True


def _fetch(url: str) -> requests.Response:
    response = requests.get(url, headers=BASE_HEADERS, timeout=10)
    response.raise_for_status()
    return response


def crawl(url: str, logger: logging.Logger) -> CrawlerResponse:
    try:
        logger.info('Verifying that robot.txt allows crawling URL: %s', url)

        if not _robot_allows_crawling(url, logger):
            return _generate_crawler_response(False, url, CrawlStatus.SKIPPED, None, None)

        response = _fetch(url)
        logger.info('Successfully Fetched URL: %s', url)

        crawler_res = _generate_crawler_response(True, url, CrawlStatus.CRAWLED_SUCCESS,
                                                 {
                                                     'status_code': response.status_code,
                                                     'headers': response.headers,
                                                     'text': response.text
                                                 }, None)

        return crawler_res
    except requests.HTTPError as e:
        logger.error(
            f"HTTPError while crawling '{url}' - StatusCode: {e.response.status_code} - {e}"
        )
        return _generate_crawler_response(False, url, CrawlStatus.CRAWL_FAILED,
                                          e.response.status_code,
                                          {
                                              'type': e.__class__.__name__,
                                              'message': str(e)
                                          })
    except requests.RequestException as e:
        logger.error(
            f"Error while crawling '{url}' - {e}"
        )
        return _generate_crawler_response(False, url, CrawlStatus.CRAWL_FAILED, None, {
            'type': e.__class__.__name__,
            'message': str(e)
        })

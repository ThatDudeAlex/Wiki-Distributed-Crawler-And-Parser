import pytest
import requests
from database.db_models.models import CrawlStatus
import services.crawler.domain.crawler as crawler
from unittest.mock import MagicMock, patch
from shared.config import BASE_HEADERS


@patch('services.crawler.domain.crawler.requests.get')
def test_fetch_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    got = crawler._fetch("http://example.com")
    assert got.status_code == 200


@patch('services.crawler.domain.crawler.requests.get')
def test_fetch_raises_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Testing")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError) as raised_error:
        crawler._fetch("http://example.com")
    assert str(raised_error.value) == "Testing"


@patch('services.crawler.domain.crawler.ROBOT_PARSER')
def test_robot_allows_crawling_true(mock_robot_parser):
    mock_robot_parser.can_fetch.return_value = True
    logger = MagicMock()
    assert crawler._robot_allows_crawling("http://example.com", logger) is True


@patch('services.crawler.domain.crawler.ROBOT_PARSER')
def test_robot_allows_crawling_false(mock_robot_parser):
    mock_robot_parser.can_fetch.return_value = False
    logger = MagicMock()
    assert crawler._robot_allows_crawling(
        "http://example.com", logger) is False


def test_generate_crawler_response():
    test_input = {
        'success': True,
        'url': 'http://example.com',
        'crawl_status': CrawlStatus.CRAWLED_SUCCESS,
        'data': {'status_code': 200},
        'error': None
    }
    got = crawler._generate_crawler_response(**test_input)
    assert got['success'] is True
    assert got['url'] == 'http://example.com'
    assert got['crawl_status'] == CrawlStatus.CRAWLED_SUCCESS
    assert got['data']['status_code'] == 200
    assert got['error'] is None


@patch('services.crawler.domain.crawler._fetch')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_success(mock_robot_check, mock_fetch):
    url = "http://example.com"
    logger = MagicMock()
    mock_robot_check.return_value = False

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = BASE_HEADERS
    mock_response.text = "mock_text"
    mock_fetch.return_value = mock_response

    got = crawler.crawl(url, logger)
    assert got['success'] is True
    assert got['crawl_status'] == CrawlStatus.CRAWLED_SUCCESS
    assert got['data']['status_code'] == 200
    assert got['data']['text'] == "mock_text"
    assert got['error'] is None


@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_robot_blocks(mock_robot_check):
    url = "http://example.com"
    logger = MagicMock()
    mock_robot_check.return_value = True

    got = crawler.crawl(url, logger)
    assert got['success'] is False
    assert got['crawl_status'] == CrawlStatus.SKIPPED
    assert got['data'] is None
    assert got['error'] is None


@patch('services.crawler.domain.crawler._fetch')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_http_error(mock_robot_check, mock_fetch):
    url = "http://example.com"
    logger = MagicMock()
    mock_robot_check.return_value = False

    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = requests.HTTPError("Not Found")
    http_error.response = mock_response
    mock_fetch.side_effect = http_error

    got = crawler.crawl(url, logger)
    assert got['success'] is False
    assert got['crawl_status'] == CrawlStatus.CRAWL_FAILED
    assert got['error']['type'] == 'HTTPError'
    assert got['error']['message'] == 'Not Found'


@patch('services.crawler.domain.crawler._fetch')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_request_exception(mock_robot_check, mock_fetch):
    url = "http://example.com"
    logger = MagicMock()
    mock_robot_check.return_value = False

    mock_fetch.side_effect = requests.Timeout("Request timed out")

    got = crawler.crawl(url, logger)
    assert got['success'] is False
    assert got['crawl_status'] == CrawlStatus.CRAWL_FAILED
    assert got['error']['type'] == 'Timeout'
    assert got['error']['message'] == 'Request timed out'

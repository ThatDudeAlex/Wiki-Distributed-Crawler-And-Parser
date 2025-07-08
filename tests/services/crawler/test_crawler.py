import pytest
import requests
from shared.rabbitmq.enums.crawl_status import CrawlStatus

import components.crawler.core.crawler as crawler
from unittest.mock import MagicMock, patch
from shared.config import BASE_HEADERS


@patch('components.crawler.core.crawler.requests.get')
def test_fetch_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    got = crawler._fetch("http://example.com")
    print(got)
    assert got.status_code == 200


@patch('components.crawler.core.crawler.requests.get')
def test_fetch_raises_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Testing")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError) as raised_error:
        crawler._fetch("http://example.com")
    assert str(raised_error.value) == "Testing"


@patch('components.crawler.core.crawler._fetch')
def test_crawl_success(mock_fetch):
    url = "http://example.com"
    logger = MagicMock()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = BASE_HEADERS
    mock_response.text = "mock_text"
    mock_fetch.return_value = mock_response

    got = crawler.crawl(url, logger)
    assert got.success is True
    assert got.crawl_status == CrawlStatus.SUCCESS
    assert got.status_code == 200
    assert got.text == "mock_text"
    assert got.error_type is None
    assert got.error_message is None


@patch('components.crawler.core.crawler._fetch')
def test_crawl_http_error(mock_fetch):
    url = "http://example.com"
    logger = MagicMock()

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.text = 'Not Found'

    http_error = requests.HTTPError("Not Found")
    http_error.response = mock_response

    mock_fetch.side_effect = http_error

    got = crawler.crawl(url, logger)

    assert got.success is False
    assert got.crawl_status == CrawlStatus.FAILED
    assert got.error_type == 'HTTPError'
    assert got.error_message == 'Not Found'


@patch('components.crawler.core.crawler._fetch')
def test_crawl_request_exception(mock_fetch):
    url = "http://example.com"
    logger = MagicMock()
    mock_fetch.side_effect = requests.Timeout("Request timed out")

    got = crawler.crawl(url, logger)

    assert got.success is False
    assert got.crawl_status == CrawlStatus.FAILED
    assert got.error_type == 'Timeout'
    assert got.error_message == 'Request timed out'


# TODO: Move robot unit test to scheduler

# @patch('urllib.robotparser.RobotFileParser')
# def test_robot_blocks_crawling_true(mock_robot_parser_class):
#     mock_robot_parser = MagicMock()
#     mock_robot_parser.can_fetch.return_value = False
#     mock_robot_parser_class.return_value = mock_robot_parser

#     logger = MagicMock()
#     assert crawler._robot_blocks_crawling("http://example.com", logger) is True


# @patch('urllib.robotparser.RobotFileParser')
# def test_robot_blocks_crawling_false(mock_robot_parser_class):
#     mock_robot_parser = MagicMock()
#     mock_robot_parser.can_fetch.return_value = True
#     mock_robot_parser_class.return_value = mock_robot_parser

#     logger = MagicMock()
#     assert crawler._robot_blocks_crawling(
#         "http://example.com", logger) is False


# @patch('components.crawler.core.crawler._robot_blocks_crawling')
# def test_crawl_robot_blocks(mock_robot_check):
#     url = "http://example.com"
#     logger = MagicMock()
#     mock_robot_check.return_value = True

#     got = crawler.crawl(url, logger)
#     assert got.success is False
#     assert got.crawl_status == CrawlStatus.SKIPPED
#     assert got.data is None
#     assert got.error is None

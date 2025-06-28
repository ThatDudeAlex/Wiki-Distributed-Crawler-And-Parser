import pytest
import requests
from database.db_models.models import CrawlStatus
import services.crawler.domain.crawler as crawler
from unittest.mock import MagicMock, Mock, patch
from shared.config import BASE_HEADERS


@patch('services.crawler.domain.crawler.requests.get')
def test_fetch(mock_get):
    # Setup
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Act
    got = crawler._fetch("http://example.com")

    # Assert
    mock_get.assert_called_once_with(
        "http://example.com",
        headers=BASE_HEADERS,
        timeout=10
    )
    assert got == mock_response


@patch('services.crawler.domain.crawler.requests.get')
def test_fetch_throws_http_error(mock_get):
    # Setup
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("Testing")
    mock_get.return_value = mock_response

    # Act & Assert
    with pytest.raises(requests.HTTPError) as raised_error:
        crawler._fetch("http://example.com")

    assert str(raised_error.value) == "Testing"


@patch('services.crawler.domain.crawler.ROBOT_PARSER')
def test_robot_allows_crawling(mock_robot_parser):
    # Setup
    mock_robot_parser.can_fetch.return_value = True
    logger = Mock()

    # Act
    allowed = crawler._robot_allows_crawling("http://example.com", logger)

    # Assert
    mock_robot_parser.can_fetch.assert_called_once()
    assert allowed is True


@patch('services.crawler.domain.crawler.ROBOT_PARSER')
def test_robot_disallows_crawling(mock_parser):
    # Setup
    mock_parser.can_fetch.return_value = False
    logger = Mock()

    # Act
    allowed = crawler._robot_allows_crawling("http://example.com", logger)

    # Assert
    mock_parser.can_fetch.assert_called_once()
    logger.warning.assert_called_once_with(
        "robots.txt blocked crawling: http://example.com")
    assert allowed is False


def test_generate_crawler_response():
    # Setup
    test_runs = [
        {
            'success': True, 'crawl_status': CrawlStatus.CRAWLED_SUCCESS,
            'data': None, 'error': None
        },
        {
            'success': False, 'crawl_status': CrawlStatus.SKIPPED,
            'data': None, 'error': None
        },
    ]

    # # Act & Assert
    for test in test_runs:
        expect = {**test}
        got = crawler._generate_crawler_response(**test)
        assert expect == got


@patch('services.crawler.domain.crawler._generate_crawler_response')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
@patch('services.crawler.domain.crawler._fetch')
def test_crawl_fetch_success(mock_fetch, mock_robot_check, mock_generate):
    logger = Mock()
    mock_robot_check.return_value = False

    # Setup
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = BASE_HEADERS
    mock_response.text = "mock_response_text"
    mock_fetch.return_value = mock_response

    expected = {
        'success': True,
        'crawl_status': CrawlStatus.CRAWLED_SUCCESS,
        'data': {
            'status_code': 200,
            'headers': BASE_HEADERS,
            'text': "mock_response_text"
        },
        'error': None
    }

    mock_generate.return_value = expected

    # Act
    got = crawler.crawl("http://example.com", logger)

    # Assert
    mock_generate.assert_called_once_with(
        True,
        CrawlStatus.CRAWLED_SUCCESS,
        {
            'status_code': 200,
            'headers': BASE_HEADERS,
            'text': "mock_response_text"
        },
        None
    )

    assert got == expected


@patch('services.crawler.domain.crawler._robot_allows_crawling')
@patch('services.crawler.domain.crawler._generate_crawler_response')
def test_crawl_robot_blocks(mock_generate, mock_robot_check):
    # Setup
    mock_robot_check.return_value = True
    mock_generate.return_value = "mocked_response"
    logger = Mock()

    # Act
    got = crawler.crawl("http://example.com", logger)

    # Assert
    mock_generate.assert_called_once_with(
        False, CrawlStatus.SKIPPED, None, None)
    assert got == "mocked_response"


@patch('services.crawler.domain.crawler._generate_crawler_response')
@patch('services.crawler.domain.crawler._fetch')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_http_error(mock_robot_check, mock_fetch, mock_generate):
    url = "http://example.com"
    logger = Mock()

    # Setup
    mock_robot_check.return_value = False    # allow crawling

    # simulate _fetch raising HTTPError with a response
    mock_response = Mock()
    mock_response.status_code = 404
    http_error = requests.HTTPError("Not Found")
    http_error.response = mock_response
    mock_fetch.side_effect = http_error

    expected = {
        'success': False,
        'crawl_status': CrawlStatus.CRAWL_FAILED,
        'data': None,
        'error': {
            'type': 'HTTPError',
            'message': 'Not Found'
        }
    }
    mock_generate.return_value = expected

    # Act
    got = crawler.crawl(url, logger)

    # Assert
    mock_generate.assert_called_once_with(
        False,
        CrawlStatus.CRAWL_FAILED,
        None,
        {
            'type': 'HTTPError',
            'message': 'Not Found'
        }
    )
    logger.error.assert_called_once_with(
        f"HTTPError while crawling '{url}' - StatusCode: 404 - Not Found"
    )
    assert got == expected


@patch('services.crawler.domain.crawler._generate_crawler_response')
@patch('services.crawler.domain.crawler._fetch')
@patch('services.crawler.domain.crawler._robot_allows_crawling')
def test_crawl_request_exception(mock_robot_check, mock_fetch, mock_generate):
    # Setup
    url = "http://example.com"
    logger = Mock()

    mock_robot_check.return_value = False   # Allow crawling

    # Simulate a generic RequestException,like Timeout
    error = requests.Timeout("Request timed out")
    mock_fetch.side_effect = error

    expected = {
        'success': False,
        'crawl_status': CrawlStatus.CRAWL_FAILED,
        'data': None,
        'error': {
            'type': 'Timeout',
            'message': 'Request timed out'
        }
    }
    mock_generate.return_value = expected

    # Act
    got = crawler.crawl(url, logger)

    # Assert
    logger.error.assert_called_once_with(
        f"Error while crawling '{url}' - Request timed out")
    mock_generate.assert_called_once_with(
        False,
        CrawlStatus.CRAWL_FAILED,
        None,
        {'type': 'Timeout', 'message': 'Request timed out'}
    )
    assert got == expected

import pytest
import pytest
from unittest.mock import MagicMock, patch
from requests import Response, HTTPError, Timeout
from components.crawler.core.http_fetcher import HttpFetcher
from components.crawler.types.crawler_types import CrawlerErrorType
from shared.configs.config_loader import component_config_loader
from shared.rabbitmq.enums.crawl_status import CrawlStatus

@pytest.fixture
def configs():
    return component_config_loader("crawler")

@pytest.fixture
def http_fetcher(configs):
    logger = MagicMock()
    return HttpFetcher(configs, logger)


def test_rate_limited_fetch_success(http_fetcher):
    # Setup
    url = "http://example.com"
    
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = 200
    mock_response.text = "OK"
    
    with patch("components.crawler.core.http_fetcher.requests.get", return_value=mock_response) as mock_get:
        # Act
        result = http_fetcher._rate_limited_fetch(url)

    # Assert
    assert result.status_code == 200
    assert result.text == "OK"
    mock_get.assert_called_once()

    args, kwargs = mock_get.call_args
    assert args[0] == url
    assert kwargs["headers"] == http_fetcher.headers
    assert kwargs["timeout"] == http_fetcher.timeout


def test_crawl_url_success(http_fetcher):
    # Setup
    fetcher = http_fetcher

    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = "<html>Test</html>"

    fetcher._rate_limited_fetch = MagicMock(return_value=mock_response)

    # Act
    result = fetcher.crawl_url("http://example.com")

    # Assert
    fetcher._rate_limited_fetch.assert_called_once_with("http://example.com")
    assert result.success is True
    assert result.crawl_status == CrawlStatus.SUCCESS
    assert result.status_code == 200
    assert result.text == "<html>Test</html>"
    assert result.headers == {"Content-Type": "text/html"}


def test_crawl_url_failure(http_fetcher):
    # Setup
    fetcher = http_fetcher

    # Simulate a timeout during fetch
    fetcher._rate_limited_fetch = MagicMock(side_effect=Timeout("Connection timed out"))

    # Act
    result = fetcher.crawl_url("http://example.com")

    # Assert
    fetcher._rate_limited_fetch.assert_called_once_with("http://example.com")
    assert result.success is False
    assert result.crawl_status == CrawlStatus.FAILED
    assert result.error_type == CrawlerErrorType.TIMEOUT
    assert "Connection timed out" in result.error_message

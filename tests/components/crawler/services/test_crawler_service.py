from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from components.crawler.services.crawler_service import CrawlerService
from components.crawler.types.crawler_types import FetchResponse
from shared.configs.config_loader import component_config_loader
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.crawling import CrawlTask
from datetime import datetime, timedelta

# TODO: update with new config_loader and remove this
# from components.crawler.configs.crawler_config import configs as loaded_configs

# Gets the root of the project relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def crawl_task():
    return CrawlTask(
        url="http://example.com",
        depth=1,
        scheduled_at='2025-07-08T12:00:00Z'
    )

@pytest.fixture
def configs():
    return component_config_loader("crawler")


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_queue_service():
    return MagicMock()


@pytest.fixture
def crawler_service(configs, mock_queue_service, mock_logger):
    return CrawlerService(
        configs=configs,
        queue_service=mock_queue_service,
        logger=mock_logger
    )



@pytest.fixture
def mock_publisher():
    publisher = MagicMock()
    return publisher


def test_config_loaded(crawler_service):
    assert crawler_service.configs is not None
    assert crawler_service.configs['rate_limit'] is not None
    assert crawler_service.configs['recrawl_interval'] is not None
    assert crawler_service.configs['storage_path'] is not None


@pytest.mark.parametrize(
    "mock_fetch_response, expected_result",
    [
        (
            FetchResponse(
                url="http://example.com",
                text="<html>OK</html>",
                success=True,
                crawl_status=CrawlStatus.SUCCESS,
                error_type=None,
                error_message=None,
                headers={"Content-Type": "text/html"},
                status_code=200
            ),
            True, # expects a response
        ),
        (
            FetchResponse(
                url="http://example.com",
                text=None,
                success=False,
                crawl_status=CrawlStatus.FAILED,
                error_type="TimeoutError",
                error_message="Request timed out",
                headers=None,
                status_code=None
            ),
            False,  # expects None to be returned
        )
    ]
)
def test_fetch_page(crawler_service, mock_fetch_response, expected_result):
    # Setup
    crawler_service.http_fetcher = MagicMock()
    crawler_service.http_fetcher.crawl_url.return_value = mock_fetch_response
    crawler_service.publisher = MagicMock()

    # Act
    result = crawler_service._fetch_page("http://test.com")

    # Assert
    if expected_result:
        assert result == mock_fetch_response
    else:
        assert result is None


@pytest.mark.parametrize(
    "side_effect, expect_exception",
    [
        # Success case: returns a tuple
        (("abc123", "/tmp/abc123.html.gz"), False),

        # Failure case: raises OSError every time
        (OSError("disk write failed"), True),
    ]
)
def test_download_compressed_html(crawler_service, side_effect, expect_exception):
    with patch("components.crawler.services.crawler_service.download_compressed_html_content") as mock_download:
        # Setup
        if expect_exception:
            mock_download.side_effect = OSError("disk write failed")
        else:
            mock_download.return_value = side_effect

        # Act & Assert
        if expect_exception:
            with pytest.raises(OSError):
                crawler_service._download_compressed_html("http://example.com", "<html></html>")
            assert mock_download.call_count == crawler_service.configs['download_retry']['attempts'] + 1
        else:
            result = crawler_service._download_compressed_html("http://example.com", "<html></html>")
            assert result == side_effect
            assert mock_download.call_count == 1


def test_get_crawl_timestamps_isoformat(crawler_service):
    # Setup
    fixed_now = "2025-07-24T12:00:00"
    recrawl_seconds = crawler_service.configs['recrawl_interval']

    # Patch the timestamp utility to return fixed_time
    with patch("components.crawler.services.crawler_service.get_timestamp_eastern_time", return_value=fixed_now):
        # Act
        fetched_at, next_crawl = crawler_service._get_crawl_timestamps_isoformat()

        # Assert
        assert fetched_at == fixed_now

    
        fetched_dt = datetime.fromisoformat(fetched_at)
        next_crawl_dt = datetime.fromisoformat(next_crawl)
        delta = next_crawl_dt - fetched_dt

        # Make sure the delta is correct
        assert delta == timedelta(seconds=recrawl_seconds)


def test_run_success(crawler_service, crawl_task):
    # Setup
    crawler = crawler_service

    crawler._fetch_page = MagicMock(return_value=MagicMock(text="<html>OK</html>", url="http://example.com"))
    crawler._download_compressed_html = MagicMock(return_value=("abc123", "/tmp/abc123.html.gz"))
    crawler._get_crawl_timestamps_isoformat = MagicMock(return_value=("2025-07-24T12:00:00", "2025-07-24T13:00:00"))
    crawler.publisher = MagicMock()

    with patch("components.crawler.services.crawler_service.PAGE_CRAWL_LATENCY_SECONDS"), \
         patch("components.crawler.services.crawler_service.CRAWL_PAGES_TOTAL"):
        # Act
        crawler.run(crawl_task)

    # Assert
    crawler._fetch_page.assert_called_once()
    crawler._download_compressed_html.assert_called_once()
    crawler.publisher.store_successful_crawl.assert_called_once()
    crawler.publisher.publish_parsing_task.assert_called_once()


def test_run_fetch_failure(crawler_service, crawl_task):
    # Setup
    crawler = crawler_service
    crawler._fetch_page = MagicMock(return_value=None)
    crawler.publisher = MagicMock()

    with patch("components.crawler.services.crawler_service.CRAWL_PAGES_TOTAL") as mock_total, \
         patch("components.crawler.services.crawler_service.PAGE_CRAWL_LATENCY_SECONDS"):
        # Act
        crawler.run(crawl_task)

    # Assert
    crawler._fetch_page.assert_called_once()
    crawler.publisher.store_successful_crawl.assert_not_called()
    crawler.publisher.publish_parsing_task.assert_not_called()
    mock_total.labels().inc.assert_called_once()


def test_run_raises_unexpected_exception(crawler_service, crawl_task):
    # Setup
    crawler = crawler_service
    crawler._fetch_page = MagicMock(return_value=MagicMock(text="<html>OK</html>"))
    crawler._download_compressed_html = MagicMock(side_effect=OSError("disk error"))
    crawler.publisher = MagicMock()

    with patch("components.crawler.services.crawler_service.CRAWL_PAGES_TOTAL") as mock_total, \
         patch("components.crawler.services.crawler_service.CRAWL_PAGES_FAILURES_TOTAL") as mock_fail, \
         patch("components.crawler.services.crawler_service.PAGE_CRAWL_LATENCY_SECONDS"):
        # Act
        crawler.run(crawl_task)

    # Assert
    crawler._fetch_page.assert_called_once()
    crawler._download_compressed_html.assert_called_once()
    mock_fail.labels.return_value.inc.assert_called_once()
    mock_total.labels.return_value.inc.assert_called_once()
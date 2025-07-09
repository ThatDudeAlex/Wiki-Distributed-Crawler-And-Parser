from zoneinfo import ZoneInfo
import pytest
from unittest.mock import MagicMock, patch
from components.crawler.services.crawler_service import CrawlerService
from components.crawler.types.crawler_types import FetchResponse
from components.crawler.types.config_types import CrawlerConfig
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
# from shared.config_loader import get_settings
from datetime import datetime
# from components.crawler.configs.crawler_config import configs as loaded_configs
from shared.configs.load_config import Path, load_config

# Gets the root of the project relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def crawl_task():
    return CrawlTask(
        url="http://example.com",
        depth=1,
        scheduled_at=datetime.fromisoformat(
            '2025-07-08T12:00:00Z')
    )


@pytest.fixture
def crawler_config() -> CrawlerConfig:
    config_path = PROJECT_ROOT.joinpath(
        "components", "crawler", "configs", "crawler_config.yml"
    )
    configs: CrawlerConfig = load_config(config_path)
    configs.storage_path = 'test-path'
    return configs


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_queue_service():
    return MagicMock()


@pytest.fixture
def mock_publisher():
    publisher = MagicMock()
    return publisher


def test_config_loaded(mock_logger, mock_queue_service, crawler_config):
    service = CrawlerService(
        configs=crawler_config, queue_service=mock_queue_service, logger=mock_logger
    )
    assert service._configs is not None
    assert service._configs.rate_limit is not None
    assert service._configs.heartbeat is not None
    assert service._configs.headers is not None


def test_run_success_path(crawl_task, mock_logger, mock_queue_service, mock_publisher, crawler_config):
    html_content = "<html>test</html>"

    with patch("components.crawler.services.crawler_service.crawl") as mock_crawl, \
            patch("components.crawler.services.crawler_service.create_hash") as mock_create_hash, \
            patch("components.crawler.services.crawler_service.download_compressed_html_content") as mock_download, \
            patch("components.crawler.services.crawler_service.get_timestamp_eastern_time") as mock_timestamp:

        # Setup
        mock_crawl.return_value = FetchResponse(
            success=True,
            url=crawl_task.url,
            crawl_status=CrawlStatus.SUCCESS,
            status_code=200,
            headers={},
            text=html_content
        )
        mock_create_hash.return_value = "html_hash"
        mock_download.return_value = ("url_hash", "/tmp/file.html")
        mock_timestamp.return_value = "2025-07-08T12:00:00Z"

        service = CrawlerService(
            crawler_config, queue_service=mock_queue_service, logger=mock_logger)
        service.publisher = mock_publisher

        # Act
        service.run(crawl_task)

        # Assert
        mock_crawl.assert_called_once_with(crawl_task.url, mock_logger)
        mock_create_hash.assert_called_once_with(html_content)
        mock_download.assert_called_once()
        mock_timestamp.assert_called()
        mock_publisher.store_successful_crawl.assert_called_once()
        mock_publisher.publish_parsing_task.assert_called_once_with(
            crawl_task.url, crawl_task.depth, "/tmp/file.html"
        )


def test_run_failed_crawl(crawl_task, mock_logger, mock_queue_service, mock_publisher, crawler_config):
    with patch("components.crawler.services.crawler_service.crawl") as mock_crawl, \
            patch("components.crawler.services.crawler_service.get_timestamp_eastern_time") as mock_timestamp:

        # Setup
        mock_crawl.return_value = FetchResponse(
            success=False,
            url=crawl_task.url,
            crawl_status=CrawlStatus.FAILED,
            error_type="Timeout",
            error_message="Request timed out"
        )
        mock_timestamp.return_value = "2025-07-08T12:00:00Z"

        service = CrawlerService(
            crawler_config, queue_service=mock_queue_service, logger=mock_logger)
        service.publisher = mock_publisher

        # Act
        service.run(crawl_task)

        # Assert
        mock_crawl.assert_called_once_with(crawl_task.url, mock_logger)
        mock_timestamp.assert_called_once()
        mock_publisher.store_failed_crawl.assert_called_once_with(
            crawl_task.url,
            CrawlStatus.FAILED,
            "2025-07-08T12:00:00Z",
            "Timeout",
            "Request timed out"
        )
        mock_publisher.store_successful_crawl.assert_not_called()
        mock_publisher.publish_parsing_task.assert_not_called()

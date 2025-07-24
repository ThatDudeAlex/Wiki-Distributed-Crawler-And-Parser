from unittest.mock import MagicMock, patch
from components.crawler.services.publisher import PublishingService
from components.crawler.types.crawler_types import FetchResponse
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.save_to_db import SavePageMetadataTask

TEST_FETCHED_AT = "2025-07-24T12:00:00"

# == Test cases for _publish_page_metadata() ==

def test_publish_page_metadata_success():
    # Setup
    mock_queue_service = MagicMock()
    mock_logger = MagicMock()
    publisher = PublishingService(mock_queue_service, mock_logger)

    message = SavePageMetadataTask(
        url="http://example.com",
        status=CrawlStatus.SUCCESS,
        fetched_at=TEST_FETCHED_AT,
        next_crawl="2025-07-25T12:00:00",
        http_status_code=200,
        url_hash="abc123",
        html_content_hash="def456",
        compressed_filepath="/tmp/example.html.gz"
    )

    # Act
    publisher._publish_page_metadata(message)

    # Assert
    mock_queue_service.publish.assert_called_once_with(
        CrawlerQueueChannels.PAGE_METADATA_TO_SAVE.value,
        message.model_dump_json()
    )
    mock_logger.info.assert_called_once_with("Published: Page Metadata - Success")


def test_publish_page_metadata_failure():
    # Setup
    mock_queue_service = MagicMock()
    mock_logger = MagicMock()
    publisher = PublishingService(mock_queue_service, mock_logger)

    message = SavePageMetadataTask(
        url="http://example.com",
        status=CrawlStatus.FAILED,
        fetched_at=TEST_FETCHED_AT,
        error_type="TimeoutError",
        error_message="Request timed out"
    )

    # Act
    publisher._publish_page_metadata(message)

    # Assert
    mock_queue_service.publish.assert_called_once_with(
        CrawlerQueueChannels.PAGE_METADATA_TO_SAVE.value,
        message.model_dump_json()
    )
    mock_logger.info.assert_called_once_with("Published: Page Metadata - Failed Crawl")


def test_publish_page_metadata_raises_exception():
    # Setup
    mock_queue_service = MagicMock()
    mock_logger = MagicMock()
    publisher = PublishingService(mock_queue_service, mock_logger)

    message = SavePageMetadataTask(
        url="http://example.com",
        status=CrawlStatus.SUCCESS,
        fetched_at=TEST_FETCHED_AT
    )

    mock_queue_service.publish.side_effect = RuntimeError("RabbitMQ down")

    # Act
    publisher._publish_page_metadata(message)

    # Assert
    mock_logger.error.assert_called_once()
    mock_logger.info.assert_not_called()  # Because publishing failed


# == Test cases for store_failed_crawl() ==

def test_store_failed_crawl():
    # Setup
    mock_queue_service = MagicMock()
    mock_logger = MagicMock()
    publisher = PublishingService(mock_queue_service, mock_logger)

    with patch.object(publisher, "_publish_page_metadata") as mock_publish:
        url = "http://example.com"
        status = CrawlStatus.FAILED
        fetched_at = TEST_FETCHED_AT
        error_type = "TimeoutError"
        error_message = "Request timed out"

        # Act
        publisher.store_failed_crawl(
            status=status,
            fetched_at=fetched_at,
            url=url,
            error_type=error_type,
            error_message=error_message
        )

        # Assert
        mock_publish.assert_called_once()
        message: SavePageMetadataTask = mock_publish.call_args[0][0]

        assert message.status == CrawlStatus.FAILED
        assert message.fetched_at == fetched_at
        assert message.url == url
        assert message.error_type == error_type
        assert message.error_message == error_message


# == Test cases for store_successful_crawl() ==

def test_store_successful_crawl():
    # Setup
    mock_queue_service = MagicMock()
    mock_logger = MagicMock()
    publisher = PublishingService(mock_queue_service, mock_logger)

    with patch.object(publisher, "_publish_page_metadata") as mock_publish:
        # FetchResponse mock
        fetch_response = FetchResponse(
            url="http://example.com",
            text="<html>Success</html>",
            success=True,
            crawl_status=CrawlStatus.SUCCESS,
            error_type=None,
            error_message=None,
            status_code=200,
            headers={"Content-Type": "text/html"}
        )

        url_hash = "abc123"
        html_content_hash = "def456"
        filepath = "/tmp/example.html.gz"
        fetched_at = TEST_FETCHED_AT
        next_crawl = "2025-07-25T12:00:00"

        # Act
        publisher.store_successful_crawl(
            fetched_response=fetch_response,
            url_hash=url_hash,
            html_content_hash=html_content_hash,
            compressed_filepath=filepath,
            fetched_at=fetched_at,
            next_crawl=next_crawl
        )

        # Assert
        mock_publish.assert_called_once()
        message: SavePageMetadataTask = mock_publish.call_args[0][0]

        assert message.status == CrawlStatus.SUCCESS
        assert message.fetched_at == fetched_at
        assert message.next_crawl == next_crawl
        assert message.url == fetch_response.url
        assert message.http_status_code == 200
        assert message.url_hash == url_hash
        assert message.html_content_hash == html_content_hash
        assert message.compressed_filepath == filepath

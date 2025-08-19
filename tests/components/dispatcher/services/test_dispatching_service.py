import pytest
from unittest.mock import MagicMock, patch
from components.dispatcher.services.dispatching_service import Dispatcher
from shared.configs.config_loader import component_config_loader
from shared.rabbitmq.schemas.crawling import CrawlTask


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_queue_service():
    return MagicMock()


@pytest.fixture
def configs():
    return component_config_loader("dispatcher")


@pytest.fixture
def mock_dispatcher(configs, mock_queue_service, mock_logger):
    service = Dispatcher(configs, mock_queue_service, mock_logger)
    service._publisher = MagicMock()
    service._dbclient = MagicMock()
    return service



@patch("components.dispatcher.services.dispatching_service.DBReaderClient")
@patch("components.dispatcher.services.dispatching_service.PublishingService")
def test_dispatcher_init_seeds_if_tables_empty(
    mock_publisher_cls, mock_db_cls, mock_queue_service,
    mock_logger, configs
):

    # Setup
    mock_db = MagicMock()
    mock_db.tables_are_empty.return_value = True
    mock_db_cls.return_value = mock_db

    mock_publisher = MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    # Act
    Dispatcher(configs, mock_queue_service, mock_logger)

    # Assert
    mock_publisher.publish_crawl_tasks.assert_called_once()
    mock_db.tables_are_empty.assert_called_once()


@patch("components.dispatcher.services.dispatching_service.DBReaderClient")
@patch("components.dispatcher.services.dispatching_service.PublishingService")
def test_dispatcher_init_skips_seeding_if_not_empty(
    mock_publisher_cls, mock_db_cls, mock_queue_service,
    mock_logger, configs
):

    mock_db = MagicMock()
    mock_db.tables_are_empty.return_value = False
    mock_db_cls.return_value = mock_db

    mock_publisher = MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    Dispatcher(configs, mock_queue_service, mock_logger)

    mock_publisher.publish_crawl_tasks.assert_not_called()


@patch("components.dispatcher.services.dispatching_service.get_timestamp_eastern_time")
@patch("components.dispatcher.services.dispatching_service.PublishingService")
@patch("components.dispatcher.services.dispatching_service.DBReaderClient")
def test_seed_empty_queue_creates_and_publishes_tasks(
    mock_db_cls, mock_publisher_cls, mock_timestamp, mock_logger
):
    mock_db = MagicMock()
    mock_db.tables_are_empty.return_value = False
    mock_db_cls.return_value = mock_db

    mock_publisher = MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    mock_timestamp.return_value = "2025-07-25T00:00:00Z"

    configs = {
        "db_reader_timeout_seconds": 5,
        "seed_urls": ["https://a.com", "https://b.com"]
    }

    dispatcher = Dispatcher(configs, MagicMock(), mock_logger)
    dispatcher.seed_empty_queue()

    expected_tasks = [
        CrawlTask(url="https://a.com", depth=0, scheduled_at="2025-07-25T00:00:00Z"),
        CrawlTask(url="https://b.com", depth=0, scheduled_at="2025-07-25T00:00:00Z")
    ]
    mock_publisher.publish_crawl_tasks.assert_called_once_with(expected_tasks)


@patch("components.dispatcher.services.dispatching_service.DBReaderClient")
@patch("components.dispatcher.services.dispatching_service.PublishingService")
def test_dispatch_success(
    mock_publisher_cls, mock_db_cls, mock_queue_service,
    mock_logger, configs
):

    # Setup
    mock_db = MagicMock()
    mock_db.tables_are_empty.return_value = False
    mock_db_cls.return_value = mock_db

    mock_publisher = MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    service = Dispatcher(configs, mock_queue_service, mock_logger)

    links_to_dispatch = [
        {
            'url': "https://a.com",
            'scheduled_at': "2025-07-25T00:00:00Z",
            'depth': 0
        },
        {
            'url': "https://b.com",
            'scheduled_at': "2025-07-25T00:00:00Z",
            'depth': 0
        },
    ]
    expected_tasks = [
        CrawlTask(url="https://a.com", depth=0, scheduled_at="2025-07-25T00:00:00Z"),
        CrawlTask(url="https://b.com", depth=0, scheduled_at="2025-07-25T00:00:00Z")
    ]
    mock_db.pop_links_from_schedule.return_value = links_to_dispatch
    
    # Act
    service._dispatch()

    # Assert
    service._publisher.publish_crawl_tasks.assert_called_once_with(expected_tasks)


@patch("components.dispatcher.services.dispatching_service.DBReaderClient")
@patch("components.dispatcher.services.dispatching_service.PublishingService")
def test_dispatch_logs_exception(
    mock_publisher_cls, mock_db_cls, mock_queue_service,
    mock_logger, configs
):

    # Setup
    mock_db = MagicMock()
    mock_db.tables_are_empty.return_value = False
    mock_db_cls.return_value = mock_db

    mock_publisher = MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    service = Dispatcher(configs, mock_queue_service, mock_logger)

    # Setup: Simulate exception
    mock_db.pop_links_from_schedule.side_effect = Exception("DB Error")

    # Act
    service._dispatch()

    # Assert
    service._publisher.publish_crawl_tasks.assert_not_called()



import pytest
from unittest.mock import MagicMock, patch
from shared.rabbitmq.queue_service import QueueService


@pytest.fixture
def mock_queue_setup():
    with patch('shared.queue_service.pika.BlockingConnection') as mock_connection_class:

        # Create mock objects
        mock_channel = MagicMock()
        mock_connection = MagicMock()
        mock_logger = MagicMock()

        # Setup mock behaviors
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection

        yield {
            "mock_channel": mock_channel,
            "mock_connection": mock_connection,
            "mock_logger": mock_logger,
            "mock_connection_class": mock_connection_class,
        }


@patch('shared.queue_service.pika.BlockingConnection')
def test_initiate_default_retries(mock_queue_setup):
    # Setup
    service = QueueService("test1", "test2",
                           mock_queue_setup["mock_logger"])

    # Assert that attributes are set correctly
    assert service._crawl_queue_name == "test1"
    assert service._parse_queue_name == "test2"
    assert service._logger == mock_queue_setup["mock_logger"]
    assert service._retry_interval == 10
    assert service._max_retries == 6


@patch('shared.queue_service.pika.BlockingConnection')
def test_initiate_specified_retries(mock_queue_setup):
    # Setup
    service = QueueService("test1", "test2",
                           mock_queue_setup["mock_logger"], 5, 12)

    # Assert that attributes are set correctly
    assert service._crawl_queue_name == "test1"
    assert service._parse_queue_name == "test2"
    assert service._logger == mock_queue_setup["mock_logger"]
    assert service._retry_interval == 5
    assert service._max_retries == 12


# def test_publish(mock_connection_class):
@patch('shared.queue_service.pika.BlockingConnection')
def test_publish(mock_connection_class, mock_queue_setup):
    # Setup
    mock_connection_class.return_value = mock_queue_setup["mock_connection"]
    service = QueueService("test", "test2", mock_queue_setup["mock_logger"])

    # Actions
    service.publish(queue_name="test", message="hello")

    # Assertions
    mock_queue_setup["mock_channel"].basic_publish.assert_called_once()

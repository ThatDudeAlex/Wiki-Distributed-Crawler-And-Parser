import pytest
from unittest.mock import Mock, patch
from components.parser.services.publisher import PublishingService
from shared.rabbitmq.enums.queue_names import ParserQueueChannels


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_queue_service():
    return Mock()


@pytest.fixture
def publisher(mock_queue_service, mock_logger):
    return PublishingService(queue_service=mock_queue_service, logger=mock_logger)


def test_publish_save_parsed_data_success(publisher, mock_queue_service, mock_logger):
    # Setup
    mock_content = Mock()
    mock_content.source_page_url = "http://example.com"
    mock_content.model_dump_json.return_value = '{"url": "http://example.com"}'

    with patch("components.parser.services.publisher.PUBLISHED_MESSAGES_TOTAL") as mock_metric:
        # Act
        publisher.publish_save_parsed_data(mock_content)

        # Assert
        mock_queue_service.publish.assert_called_once_with(
            ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value,
            '{"url": "http://example.com"}'
        )
        mock_logger.info.assert_called_once_with(
            "Published SaveParsedContent for URL: %s", "http://example.com"
        )
        mock_metric.labels.assert_called_once_with(
            queue=ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value,
            status="success"
        )
        mock_metric.labels().inc.assert_called_once()


def test_publish_save_parsed_data_failure(publisher, mock_queue_service, mock_logger):
    # Setup
    mock_content = Mock()
    mock_content.url = "http://example.com"
    mock_content.model_dump_json.side_effect = Exception("serialization error")

    with patch("components.parser.services.publisher.PUBLISHED_MESSAGES_TOTAL") as mock_metric:
        # Act
        publisher.publish_save_parsed_data(mock_content)

        # Assert
        mock_queue_service.publish.assert_not_called()
        mock_logger.exception.assert_called_once()
        mock_metric.labels.assert_called_once_with(
            queue=ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value,
            status="failure"
        )
        mock_metric.labels().inc.assert_called_once()


def test_publish_process_links_task_success(publisher, mock_queue_service, mock_logger):
    # Setup
    mock_links = [Mock(), Mock()]
    fake_serialized_json = '{"links": [...]}'

    with patch("components.parser.services.publisher.ProcessDiscoveredLinks") as mock_model, \
         patch("components.parser.services.publisher.PUBLISHED_MESSAGES_TOTAL") as mock_metric:
        
        mock_instance = mock_model.return_value
        mock_instance.model_dump_json.return_value = fake_serialized_json

        # Act
        publisher.publish_process_links_task(mock_links)

        # Assert
        mock_model.assert_called_once_with(links=mock_links)
        mock_instance.model_dump_json.assert_called_once()

        mock_queue_service.publish.assert_called_once_with(
            ParserQueueChannels.LINKS_TO_SCHEDULE.value,
            fake_serialized_json
        )
        mock_logger.info.assert_called_once_with(
            "Published: %d Process Links To Process", len(mock_links)
        )
        mock_metric.labels.assert_called_once_with(
            queue=ParserQueueChannels.LINKS_TO_SCHEDULE.value,
            status="success"
        )
        mock_metric.labels().inc.assert_called_once()


def test_publish_process_links_task_failure(publisher, mock_queue_service, mock_logger):
    # Setup
    mock_links = [Mock()]
    
    with patch("components.parser.services.publisher.ProcessDiscoveredLinks", side_effect=Exception("boom")), \
         patch("components.parser.services.publisher.PUBLISHED_MESSAGES_TOTAL") as mock_metric:
        
        # Act
        publisher.publish_process_links_task(mock_links)

        # Assert
        mock_queue_service.publish.assert_not_called()
        mock_logger.exception.assert_called_once()
        mock_metric.labels.assert_called_once_with(
            queue=ParserQueueChannels.LINKS_TO_SCHEDULE.value,
            status="failure"
        )
        mock_metric.labels().inc.assert_called_once()

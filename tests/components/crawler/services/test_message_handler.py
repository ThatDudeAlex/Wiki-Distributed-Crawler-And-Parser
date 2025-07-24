from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from components.crawler.services.message_handler import (
    handle_crawl_message,
    parse_crawl_task,
    start_crawler_listener,
)
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.crawling import CrawlTask



# == Test cases for parse_crawl_task() ==

def test_parse_crawl_task_valid():
    # Setup
    body = b'{"url": "http://example.com", "depth": 1, "scheduled_at": "2025-07-24T12:00:00"}'

    # Act
    result = parse_crawl_task(body)

    # Assert
    assert isinstance(result, CrawlTask)
    assert result.url == "http://example.com"
    assert result.depth == 1
    assert result.scheduled_at == "2025-07-24T12:00:00"


def test_parse_crawl_task_invalid_utf8():
    # Setup
    body = b'\xff\xfe\xfd'  # Not valid UTF-8

    # Act & Assert
    with pytest.raises(UnicodeDecodeError):
        parse_crawl_task(body)


def test_parse_crawl_task_invalid_schema():
    # Setup
    body = b'{"url": "http://example.com"}'  # Missing required fields "depth" and "scheduled_at"

    # Act & Assert
    with pytest.raises(ValidationError):
        parse_crawl_task(body)


def test_parse_crawl_task_malformed_json():
    # Setup
    body = b'{"url": "http://example.com", "depth": 1, "scheduled_at":'  # Malformed JSON

    # Act & Assert
    with pytest.raises(ValueError):  # pydantic may raise generic ValueError in v2
        parse_crawl_task(body)



# == Test cases for handle_crawl_message() ==

def test_handle_message_success():
    # Setup
    task_json = b'{"url": "http://example.com", "depth": 1, "scheduled_at": "2025-07-24T12:00:00"}'

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag123"
    logger = MagicMock()
    crawler_service = MagicMock()

    # Act
    handle_crawl_message(ch, method, None, task_json, crawler_service, logger)

    # Assert
    crawler_service.run.assert_called_once()
    logger.info.assert_any_call("Initiating crawl for URL: %s", "http://example.com")
    ch.basic_ack.assert_called_once_with(delivery_tag="tag123")
    ch.basic_nack.assert_not_called()

def test_handle_message_invalid_utf8():
    # Setup
    invalid_body = b"\xff\xfe\xfd"

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag456"
    logger = MagicMock()
    crawler_service = MagicMock()

    # Act
    handle_crawl_message(ch, method, None, invalid_body, crawler_service, logger)

    # Assert
    logger.error.assert_called_once()
    ch.basic_ack.assert_not_called()
    ch.basic_nack.assert_called_once_with(delivery_tag="tag456", requeue=False)


def test_handle_message_schema_validation_error():
    # Setup
    invalid_schema = b'{"url": "http://example.com"}' # missing depth & scheduled_at

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag789"
    logger = MagicMock()
    crawler_service = MagicMock()

    # Act
    handle_crawl_message(ch, method, None, invalid_schema, crawler_service, logger)

    # Assert
    logger.error.assert_called_once()
    ch.basic_ack.assert_not_called()
    ch.basic_nack.assert_called_once_with(delivery_tag="tag789", requeue=False)


def test_handle_message_unexpected_exception():
    # Setup
    valid_body = b'{"url": "http://example.com", "depth": 1, "scheduled_at": "2025-07-24T12:00:00"}'

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag999"
    logger = MagicMock()

    # Patch crawler_service.run to raise unexpected exception
    crawler_service = MagicMock()
    crawler_service.run.side_effect = RuntimeError("Error!")

    # Act
    handle_crawl_message(ch, method, None, valid_body, crawler_service, logger)

    # Assert
    logger.exception.assert_called_once()
    ch.basic_ack.assert_not_called()
    ch.basic_nack.assert_called_once_with(delivery_tag="tag999", requeue=False)

def test_start_crawler_listener():
    # Setup
    mock_channel = MagicMock()
    mock_queue_service = MagicMock()
    mock_queue_service._channel = mock_channel

    mock_logger = MagicMock()
    mock_crawler_service = MagicMock()

    # Act
    start_crawler_listener(mock_queue_service, mock_crawler_service, mock_logger)

    # Assert
    mock_channel.basic_consume.assert_called_once()

    call_args = mock_channel.basic_consume.call_args[1]
    assert call_args["queue"] == CrawlerQueueChannels.URLS_TO_CRAWL.value
    assert call_args["auto_ack"] is False
    assert callable(call_args["on_message_callback"])  # the partial

    mock_channel.start_consuming.assert_called_once()
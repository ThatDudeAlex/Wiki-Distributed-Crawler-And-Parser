import json
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo
from components.crawler import message_handler
from shared.rabbitmq.schemas.crawling import CrawlTask
from datetime import datetime


def test_handle_message_valid():
    # 1. Setup
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc"
    properties = MagicMock()
    crawler_service = MagicMock()
    logger = MagicMock()
    scheduled = datetime.now(ZoneInfo("America/New_York"))

    # Construct valid message
    message = CrawlTask(
        url='https://example.com',
        depth=0,
        scheduled_at=scheduled
    )
    # Simulate publish
    message.validate_publish()
    body = json.dumps(message.to_dict()).encode()

    # simulate consume message
    consume_message_str = body.decode('utf-8')
    consume_message_dict = json.loads(consume_message_str)
    expected = CrawlTask(**consume_message_dict)
    expected.validate_consume()

    # 2. Act
    message_handler.run_crawler(
        ch, method, properties, body, crawler_service, logger)

    # 3. Assert
    crawler_service.run.assert_called_once_with(expected)
    ch.basic_ack.assert_called_once_with(delivery_tag="abc")


def test_handle_message_invalid_json(monkeypatch):
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc"
    properties = MagicMock()
    crawler_service = MagicMock()
    logger = MagicMock()

    # This will cause `CrawlTask(**message)` to raise ValueError
    body = json.dumps({"url": 123, "depth": "3"}).encode()

    # Patch CrawlTask to raise ValueError
    class DummyValidationError(ValueError):
        def json(self): return "Mocked validation error"

    with patch("components.crawler.message_handler.CrawlTask", side_effect=DummyValidationError()):
        message_handler.run_crawler(
            ch, method, properties, body, crawler_service, logger)

    ch.basic_nack.assert_called_once_with(delivery_tag="abc", requeue=False)


def test_handle_message_unexpected_exception():
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc"
    properties = MagicMock()
    crawler_service = MagicMock()
    logger = MagicMock()

    message_dict = {"url": "https://example.com", "depth": 1}
    body = json.dumps(message_dict).encode()

    # Simulate unexpected error
    crawler_service.run.side_effect = RuntimeError("TestError")

    message_handler.run_crawler(
        ch, method, properties, body, crawler_service, logger)

    ch.basic_nack.assert_called_once_with(delivery_tag="abc", requeue=False)

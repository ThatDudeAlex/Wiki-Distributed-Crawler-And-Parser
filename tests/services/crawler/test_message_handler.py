import json
from pydantic import HttpUrl
import pytest
from unittest.mock import MagicMock, patch
from services.crawler.domain.types import CrawlTask
from services.crawler import message_handler


def test_handle_message_valid():
    # Setup
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc"
    properties = MagicMock()
    crawler_service = MagicMock()
    logger = MagicMock()

    # Construct valid message
    message_dict = {"url": "https://example.com", "depth": 1}
    body = json.dumps(message_dict).encode()

    # Act
    message_handler.handle_message(
        ch, method, properties, body, crawler_service, logger)

    # Assert
    crawler_service.run.assert_called_once_with(
        HttpUrl("https://example.com"), 1)
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

    with patch("services.crawler.message_handler.CrawlTask", side_effect=DummyValidationError()):
        message_handler.handle_message(
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

    message_handler.handle_message(
        ch, method, properties, body, crawler_service, logger)

    ch.basic_nack.assert_called_once_with(delivery_tag="abc", requeue=False)

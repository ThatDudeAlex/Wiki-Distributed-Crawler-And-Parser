from functools import partial
import logging
import os
from unittest.mock import Mock, patch
import pytest

from components.parser.services.message_handler import handle_parsing_message, start_parser_listener
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.schemas.parsing import ParsingTask


@pytest.fixture
def fake_task(tmp_path):
    filepath = tmp_path / "sample.html.gz"
    filepath.write_text("dummy gzipped content")  # just so the file exists
    return ParsingTask(
        url="http://example.com",
        compressed_filepath=str(filepath),
        depth=1,
    )


@pytest.fixture
def mock_ch():
    return Mock()


@pytest.fixture
def mock_method():
    return Mock(delivery_tag="abc123")


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)


@patch("components.parser.services.message_handler.PARSER_MESSAGES_RECEIVED_TOTAL")
@patch("components.parser.services.message_handler.PARSER_MESSAGE_FAILURES_TOTAL")
def test_handle_valid_message(
    mock_fail_counter, mock_received_counter, fake_task, mock_ch, mock_method, mock_logger
):
    body = fake_task.model_dump_json().encode("utf-8")
    mock_parsing_service = Mock()

    handle_parsing_message(
        ch=mock_ch,
        method=mock_method,
        properties=None,
        body=body,
        parsing_service=mock_parsing_service,
        logger=mock_logger
    )

    mock_parsing_service.run.assert_called_once_with(fake_task)
    mock_ch.basic_ack.assert_called_once_with(delivery_tag="abc123")
    mock_received_counter.labels(status="valid").inc.assert_called_once()
    mock_logger.info.assert_called_with("Initiating parsing on file: %s", str(fake_task.compressed_filepath))


@patch("components.parser.services.message_handler.PARSER_MESSAGES_RECEIVED_TOTAL")
def test_handle_missing_file(
    mock_received_counter, mock_ch, mock_method, mock_logger, fake_task
):
    # Simulate missing file
    os.remove(fake_task.compressed_filepath)
    body = fake_task.model_dump_json().encode("utf-8")
    mock_parsing_service = Mock()

    handle_parsing_message(
        ch=mock_ch,
        method=mock_method,
        properties=None,
        body=body,
        parsing_service=mock_parsing_service,
        logger=mock_logger
    )

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_received_counter.labels(status="missing_file").inc.assert_called_once()
    mock_logger.warning.assert_called_once()


@patch("components.parser.services.message_handler.PARSER_MESSAGES_RECEIVED_TOTAL")
def test_handle_invalid_json(mock_received_counter, mock_ch, mock_method, mock_logger):
    body = b'{"this": "is not valid for ParsingTask"}'
    mock_parsing_service = Mock()

    handle_parsing_message(
        ch=mock_ch,
        method=mock_method,
        properties=None,
        body=body,
        parsing_service=mock_parsing_service,
        logger=mock_logger
    )

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_received_counter.labels(status="invalid").inc.assert_called_once()
    mock_logger.error.assert_called_once()


@patch("components.parser.services.message_handler.PARSER_MESSAGES_RECEIVED_TOTAL")
@patch("components.parser.services.message_handler.PARSER_MESSAGE_FAILURES_TOTAL")
def test_handle_unexpected_exception(
    mock_fail_counter, mock_received_counter, mock_ch, mock_method, mock_logger, fake_task
):
    body = fake_task.model_dump_json().encode("utf-8")

    mock_parsing_service = Mock()
    mock_parsing_service.run.side_effect = RuntimeError("Boom!")

    handle_parsing_message(
        ch=mock_ch,
        method=mock_method,
        properties=None,
        body=body,
        parsing_service=mock_parsing_service,
        logger=mock_logger
    )

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_logger.exception.assert_called_once_with("Unexpected error while processing message")
    mock_received_counter.labels(status="error").inc.assert_called_once()
    mock_fail_counter.labels(error_type="RuntimeError").inc.assert_called_once()


@patch("components.parser.services.message_handler.handle_parsing_message")
def test_start_parser_listener_sets_up_consumer(mock_handle_msg):
    # Setup
    mock_queue_service = Mock()
    mock_parsing_service = Mock()
    mock_logger = Mock(spec=logging.Logger)

    # Act
    start_parser_listener(mock_queue_service, mock_parsing_service, mock_logger)

    # Assert
    mock_queue_service._channel.basic_consume.assert_called_once()

    args, kwargs = mock_queue_service._channel.basic_consume.call_args
    assert kwargs["queue"] == ParserQueueChannels.PAGES_TO_PARSE.value
    assert kwargs["auto_ack"] is False

    on_callback = kwargs["on_message_callback"]
    assert isinstance(on_callback, partial)
    assert on_callback.func == mock_handle_msg
    assert on_callback.keywords["parsing_service"] == mock_parsing_service
    assert on_callback.keywords["logger"] == mock_logger

    mock_queue_service._channel.start_consuming.assert_called_once()

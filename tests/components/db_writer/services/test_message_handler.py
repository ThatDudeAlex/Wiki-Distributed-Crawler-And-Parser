import logging
import pytest
import json
from unittest.mock import Mock
from components.db_writer.services.message_handler import consume_add_links_to_schedule, consume_save_page_metadata, consume_save_parsed_content, consume_save_processed_links
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.save_to_db import SavePageMetadataTask, SaveParsedContent


@pytest.fixture
def mock_ch():
    return Mock()


@pytest.fixture
def mock_method():
    return Mock(delivery_tag="abc123")


@pytest.fixture
def mock_logger():
    return Mock(spec=logging.Logger)

def test_consume_save_page_metadata_valid(mock_ch, mock_method, mock_logger, mocker):

    valid_payload = {
        "status": CrawlStatus.SUCCESS.value,
        "fetched_at": "2025-07-24T12:00:00",
        "url": "https://example.com",
        "http_status_code": 200,
        "url_hash": "abcdef123456",
        "html_content_hash": "123abc456def",
        "compressed_filepath": "/tmp/example.html.gz",
        "next_crawl": "2025-08-01T12:00:00",
        "error_type": None,
        "error_message": None
    }

    mock_save = mocker.patch(
        "components.db_writer.services.message_handler.save_page_metadata"
    )

    body = json.dumps(valid_payload).encode("utf-8")

    consume_save_page_metadata(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_ack.assert_called_once_with(delivery_tag='abc123')
    mock_ch.basic_nack.assert_not_called()
    mock_save.assert_called_once_with(SavePageMetadataTask(**valid_payload), mock_logger)


def test_consume_save_page_metadata_invalid_schema(mock_ch, mock_method, mock_logger):
    # 'url' must be a string — this triggers validation failure
    invalid_payload = {
        "status": CrawlStatus.SUCCESS.value,
        "fetched_at": "2025-07-24T12:00:00",
        "url": 123,  # Invalid type
    }

    body = json.dumps(invalid_payload).encode("utf-8")

    consume_save_page_metadata(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_page_metadata_raises_unexpected_error(mock_ch, mock_method, mock_logger, mocker):
    valid_payload = {
        "status": CrawlStatus.SUCCESS.value,
        "fetched_at": "2025-07-24T12:00:00",
        "url": "https://example.com"
    }

    mocker.patch(
        "components.db_writer.services.message_handler.save_page_metadata",
        side_effect=RuntimeError("Simulated crash")
    )

    body = json.dumps(valid_payload).encode("utf-8")

    consume_save_page_metadata(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_page_metadata_triggers_value_error(mock_ch, mock_method, mock_logger):
    # Trailing comma makes it invalid JSON
    malformed_json = b'{"status": "SUCCESS", "url": "https://example.com",}'

    consume_save_page_metadata(mock_ch, mock_method, None, malformed_json, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_page_metadata_triggers_validation_error(mock_ch, mock_method, mock_logger):
    # Missing 'status' field
    incomplete_payload = {
        "fetched_at": "2025-07-24T12:00:00",
        "url": "https://example.com"
    }

    body = json.dumps(incomplete_payload).encode("utf-8")

    consume_save_page_metadata(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_parsed_content_valid(mock_ch, mock_method, mock_logger, mocker):
    valid_payload = {
        "source_page_url": "https://example.com/page",
        "title": "Example Title",
        "parsed_at": "2025-07-24T12:00:00",
        "text_content": "blah blah...",
        "text_content_hash": "abc123",
        "categories": ["History", "Culture"]
    }

    mock_save = mocker.patch(
        "components.db_writer.services.message_handler.save_parsed_data"
    )

    body = json.dumps(valid_payload).encode("utf-8")

    consume_save_parsed_content(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_ack.assert_called_once_with(delivery_tag="abc123")
    mock_ch.basic_nack.assert_not_called()
    mock_save.assert_called_once_with(SaveParsedContent(**valid_payload), mock_logger)


def test_consume_save_parsed_content_value_error(mock_ch, mock_method, mock_logger):
    invalid_payload = {
        "source_page_url": "not_a_url",  # Invalid
        "title": "Example Title",
        "parsed_at": "2025-07-24T12:00:00"
    }

    body = json.dumps(invalid_payload).encode("utf-8")

    consume_save_parsed_content(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_parsed_content_validation_error(mock_ch, mock_method, mock_logger):
    invalid_payload = {
        "source_page_url": "not_a_url",  # Invalid
        "title": "Example Title",
        "parsed_at": "2025-07-24T12:00:00"
    }

    body = json.dumps(invalid_payload).encode("utf-8")

    consume_save_parsed_content(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_parsed_content_raises_exception(mock_ch, mock_method, mock_logger, mocker):
    payload = {
        "source_page_url": "https://example.com/page",
        "title": "Title",
        "parsed_at": "2025-07-24T12:00:00"
    }

    mocker.patch(
        "components.db_writer.services.message_handler.save_parsed_data",
        side_effect=RuntimeError("Simulated error")
    )

    body = json.dumps(payload).encode("utf-8")

    consume_save_parsed_content(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_save_parsed_content_value_error(mock_ch, mock_method, mock_logger):
    malformed_json = b'{"source_page_url": "https://example.com",}'  # Trailing comma

    consume_save_parsed_content(mock_ch, mock_method, None, malformed_json, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_add_links_to_schedule_valid(mock_ch, mock_method, mock_logger, mocker):
    valid_payload = {
        "links": [
            {
                "url": "https://example.com",
                "depth": 1,
                "scheduled_at": "2025-07-24T12:00:00"
            }
        ]
    }

    mock_add = mocker.patch(
        "components.db_writer.services.message_handler.add_links_to_schedule"
    )

    body = json.dumps(valid_payload).encode("utf-8")

    consume_add_links_to_schedule(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_ack.assert_called_once_with(delivery_tag="abc123")
    mock_ch.basic_nack.assert_not_called()
    mock_add.assert_called_once()


def test_consume_save_processed_links_success(mocker, mock_ch, mock_method, mock_logger):
    mock_task = mocker.Mock()
    mocker.patch(
        "components.db_writer.services.message_handler.SaveProcessedLinks.model_validate_json",
        return_value=mock_task
    )
    mock_save = mocker.patch(
        "components.db_writer.services.message_handler.save_processed_links"
    )

    message = b'{"links": []}'  # valid minimal input

    consume_save_processed_links(mock_ch, mock_method, None, message, mock_logger)

    mock_save.assert_called_once_with(mock_task, mock_logger)
    mock_ch.basic_ack.assert_called_once_with(delivery_tag="abc123")


def test_consume_save_processed_links_value_error(mocker, mock_ch, mock_method, mock_logger):
    mocker.patch(
        "components.db_writer.services.message_handler.SaveProcessedLinks.model_validate_json",
        side_effect=ValueError("Invalid JSON format")
    )

    message = b'invalid_json'

    consume_save_processed_links(mock_ch, mock_method, None, message, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)


def test_consume_save_processed_links_unexpected_error(mocker, mock_ch, mock_method, mock_logger):
    mock_task = mocker.Mock()
    mocker.patch(
        "components.db_writer.services.message_handler.SaveProcessedLinks.model_validate_json",
        return_value=mock_task
    )

    mocker.patch(
        "components.db_writer.services.message_handler.save_processed_links",
        side_effect=RuntimeError("DB failed")
    )

    message = b'{"links": []}'

    consume_save_processed_links(mock_ch, mock_method, None, message, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)



def test_consume_add_links_to_schedule_invalid_schema(mock_ch, mock_method, mock_logger):
    payload = {
        "scheduled_links": [
            {
                "url": "not a url",
                "depth": 1,
                "scheduled_at": "2025-07-24T12:00:00"
            }
        ]
    }

    body = json.dumps(payload).encode("utf-8")

    consume_add_links_to_schedule(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_add_links_to_schedule_missing_required_field(mock_ch, mock_method, mock_logger):
    payload = {
        "scheduled_links": [
            {
                "url": "https://example.com",
                "depth": 1
                # Missing scheduled_at
            }
        ]
    }

    body = json.dumps(payload).encode("utf-8")

    consume_add_links_to_schedule(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_add_links_to_schedule_malformed_json(mock_ch, mock_method, mock_logger):
    body = b'{"scheduled_links": [ {"url": "https://example.com", }]}'

    consume_add_links_to_schedule(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


def test_consume_add_links_to_schedule_raises_unexpected_error(mock_ch, mock_method, mock_logger, mocker):
    payload = {
        "scheduled_links": [
            {
                "url": "https://example.com",
                "depth": 1,
                "scheduled_at": "2025-07-24T12:00:00"
            }
        ]
    }

    mocker.patch(
        "components.db_writer.services.message_handler.add_links_to_schedule",
        side_effect=RuntimeError("Unexpected failure")
    )

    body = json.dumps(payload).encode("utf-8")

    consume_add_links_to_schedule(mock_ch, mock_method, None, body, mock_logger)

    mock_ch.basic_nack.assert_called_once_with(delivery_tag="abc123", requeue=False)
    mock_ch.basic_ack.assert_not_called()


from components.db_writer.services.message_handler import start_db_service_listener
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels


def test_start_db_service_listener_registers_consumers_correctly(mocker, mock_logger):
    # Setup
    mock_channel = mocker.Mock()
    mock_queue_service = mocker.Mock()
    mock_queue_service._channel = mock_channel

    # Patch consumer functions to avoid running real logic
    mocker.patch.multiple(
        "components.db_writer.services.message_handler",
        consume_save_page_metadata=mocker.Mock(),
        consume_save_parsed_content=mocker.Mock(),
        consume_save_processed_links=mocker.Mock(),
        consume_add_links_to_schedule=mocker.Mock()
    )

    # Act
    start_db_service_listener(mock_queue_service, mock_logger)

    # Assert
    # all four queues registered with correct names
    assert mock_channel.basic_consume.call_count == 4

    mock_channel.basic_consume.assert_any_call(
        queue=DbWriterQueueChannels.PAGE_METADATA_TO_SAVE,
        on_message_callback=mocker.ANY,
        auto_ack=False,
    )
    mock_channel.basic_consume.assert_any_call(
        queue=DbWriterQueueChannels.PARSED_CONTENT_TO_SAVE,
        on_message_callback=mocker.ANY,
        auto_ack=False,
    )
    mock_channel.basic_consume.assert_any_call(
        queue=DbWriterQueueChannels.SCHEDULED_LINKS_TO_SAVE,
        on_message_callback=mocker.ANY,
        auto_ack=False,
    )
    mock_channel.basic_consume.assert_any_call(
        queue=DbWriterQueueChannels.ADD_LINKS_TO_SCHEDULE,
        on_message_callback=mocker.ANY,
        auto_ack=False,
    )

    mock_channel.start_consuming.assert_called_once()

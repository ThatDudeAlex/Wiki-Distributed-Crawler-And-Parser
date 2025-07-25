import pytest
from unittest.mock import MagicMock, call
from components.dispatcher.services.publisher import PublishingService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.crawling import CrawlTask


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_queue_service():
    return MagicMock()


@pytest.fixture
def publisher(mock_queue_service, mock_logger):
    return PublishingService(mock_queue_service, mock_logger)


def test_publish_all_success(publisher, mock_queue_service):
    tasks = [
        CrawlTask(url="https://example.com", depth=0, scheduled_at="2025-07-25T00:00:00Z"),
        CrawlTask(url="https://another.com", depth=1, scheduled_at="2025-07-25T00:01:00Z"),
    ]

    publisher.publish_crawl_tasks(tasks)

    # Verify .publish called once per task
    assert mock_queue_service.publish.call_count == 2

    expected_calls = [
        call(SchedulerQueueChannels.URLS_TO_CRAWL.value, tasks[0].model_dump_json()),
        call(SchedulerQueueChannels.URLS_TO_CRAWL.value, tasks[1].model_dump_json())
    ]
    mock_queue_service.publish.assert_has_calls(expected_calls, any_order=False)


def test_publish_partial_failure(publisher, mock_queue_service):
    tasks = [
        CrawlTask(url="https://example.com", depth=0, scheduled_at="2025-07-25T00:00:00Z"),
        CrawlTask(url="https://fail.com", depth=1, scheduled_at="2025-07-25T00:01:00Z"),
    ]

    # Simulate exception
    def publish_side_effect(queue, msg):
        if "fail.com" in msg:
            raise Exception("Queue error")

    mock_queue_service.publish.side_effect = publish_side_effect

    publisher.publish_crawl_tasks(tasks)

    # First publish should succeed, second should raise
    assert mock_queue_service.publish.call_count == 2

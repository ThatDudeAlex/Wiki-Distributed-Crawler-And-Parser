import logging
from typing import List
from components.rescheduler.monitoring.metrics import RESCHEDULER_CRAWL_TASKS_PUBLISHED_TOTAL, RESCHEDULER_ERRORS_TOTAL
from shared.rabbitmq.enums.queue_names import ReschedulerQueueChannels
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask


class PublishingService:
    """
    Service for publishing tasks to RabbitMQ queues

    Publishes:
        - CrawlTask messages to the 'urls_to_crawl' queue
    """
    
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger


    def publish_crawl_tasks(self, crawl_tasks: List[CrawlTask]) -> None:
        """
        Publish a list of CrawlTask messages to the 'urls_to_crawl' queue

        Each task is serialized to JSON and sent via the queue service.
        Logs the total number of tasks published.

        Args:
            crawl_tasks (List[CrawlTask]): List of CrawlTask Pydantic models to publish
        """
        successful = 0

        for task in crawl_tasks:
            try:
                self._queue_service.publish(
                    ReschedulerQueueChannels.URLS_TO_CRAWL.value, 
                    task.model_dump_json()
                )
                self._logger.debug("Published Crawl Task: %s", task)
                successful += 1
                RESCHEDULER_CRAWL_TASKS_PUBLISHED_TOTAL.labels(
                    status="success"
                ).inc()

            except Exception:
                self._logger.exception("Failed to publish crawl task")
                RESCHEDULER_ERRORS_TOTAL.inc()
                RESCHEDULER_CRAWL_TASKS_PUBLISHED_TOTAL.labels(
                    status="error"
                ).inc()

        self._logger.info("Successfully published %d out of %d crawl tasks", successful, len(crawl_tasks))


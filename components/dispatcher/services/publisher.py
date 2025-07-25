import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    """
    Service for publishing tasks to RabbitMQ queues

    Publishes:
        - CrawlTask messages to the 'urls_to_crawl' queue
    """

    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        """
        Initialize the publishing service

        Args:
            queue_service (QueueService): Service for publishing messages to RabbitMQ
            logger (logging.Logger): Logger instance
        """
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
                    SchedulerQueueChannels.URLS_TO_CRAWL.value, 
                    task.model_dump_json()
                )
                self._logger.debug("Published Crawl Task: %s", task)
                successful += 1

            except Exception:
                self._logger.exception("Failed to publish crawl task")

        self._logger.info("Successfully published %d out of %d crawl tasks", successful, len(crawl_tasks))


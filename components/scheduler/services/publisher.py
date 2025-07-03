from datetime import datetime
import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    # TODO: Scheduler - Implement retry mechanism and dead-letter
    def publish_store_processed_links(self):

        # TODO: Implement

        self._logger.info("Published: Store Processed Links")

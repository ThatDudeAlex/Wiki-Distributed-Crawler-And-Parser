"""
Publishes messages from the Scheduler component to appropriate RabbitMQ queues

Handles serialization and routing of:
    - Processed links for database storage
    - Scheduling newly discovered links for future crawling
"""

import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels, DelayQueues
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.schemas.scheduling import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.schemas.save_to_db import SaveProcessedLinks, SaveLinksToSchedule
from shared.rabbitmq.queue_service import QueueService
from shared.utils import get_timestamp_eastern_time


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger


    # TODO: Implement retry mechanism or dead-letter
    def publish_save_processed_links(self, links_to_save: List[LinkData]):
        """
        Publishes a list of processed links to the database writer queue

        Args:
            links_to_save (List[LinkData]): 
                - Newly discovered Links that have been processed, scheduled & need to be
                  added into the link graph
        """
        if not links_to_save:
            self._logger.warning("No links provided to publish_save_processed_links - skipping publish")
            return
        
        message = SaveProcessedLinks(links=links_to_save)

        self._queue_service.publish(
            SchedulerQueueChannels.SCHEDULED_LINKS_TO_SAVE.value, 
            message.model_dump_json())

        self._logger.info("Published: Save Processed Links")


    # TODO: Implement retry mechanism and dead-letter
    def publish_links_to_schedule(self, links_to_crawl: List[LinkData]):
        """
        Publishes a list of links to schedule to the database writer queue

        Args:
            links_to_crawl (List[LinkData]): Links to schedule for crawling
        """
        if not links_to_crawl:
            self._logger.warning("No links provided to publish_links_to_schedule - skipping publish")
            return
        
        scheduled_links = []
        
        for link in links_to_crawl:
            task = CrawlTask(
                url=link.url,
                scheduled_at=get_timestamp_eastern_time(isoformat=True),
                depth=link.depth
            )
            scheduled_links.append(task)

        message = SaveLinksToSchedule(links=scheduled_links)

        self._queue_service.publish(
            SchedulerQueueChannels.ADD_LINKS_TO_SCHEDULE.value, 
            message.model_dump_json())
        
        self._logger.info("Published: %s Links Scheduled", len(scheduled_links))

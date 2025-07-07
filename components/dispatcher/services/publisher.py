from datetime import datetime
import logging
from time import sleep
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels, DelayQueues
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.schemas.link_processing_schemas import CacheSeenUrls, SaveProcessedLinks, SeenUrl, AddLinksToSchedule
from shared.rabbitmq.queue_service import QueueService
from shared.utils import get_timestamp_eastern_time


# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    def publish_crawl_tasks(self, links_to_crawl: List[CrawlTask]):
        link_count = 0
        self._logger.info("Publishing links to crawl: %s", links_to_crawl)

        for link in links_to_crawl:
            message = link
            message.validate_publish()

            self._queue_service.publish(
                SchedulerQueueChannels.URLS_TO_CRAWL.value, message)
            link_count += 1

            self._logger.info("Published: %s Links To Crawl", link_count)

from datetime import datetime
import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData
from shared.rabbitmq.schemas.link_processing_schemas import CacheSeenUrls, SaveProcessedLinks, SeenUrl
from shared.rabbitmq.queue_service import QueueService
from shared.utils import get_timestamp_eastern_time


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    # TODO: Implement retry mechanism and dead-letter
    def publish_cache_urls(self, links_to_cache: List[LinkData]):
        cache_list = []

        for link in links_to_cache:
            seen_url = SeenUrl(
                link.url,
                last_seen=get_timestamp_eastern_time()
            )
            cache_list.append(seen_url)

        message = CacheSeenUrls(seen_urls=cache_list)
        message.validate_publish()

        self._queue_service.publish(
            SchedulerQueueChannels.CACHE_PROCESSED_LINKS, message)

        self._logger.info("Published: Cache Processed Links")

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_processed_links(self, links_to_save: List[LinkData]):
        message = SaveProcessedLinks(links=links_to_save)
        message.validate_publish()

        self._queue_service.publish(
            SchedulerQueueChannels.SAVE_PROCESSED_LINKS, message)

        self._logger.info("Published: Save Processed Links")

    # TODO: Implement retry mechanism and dead-letter
    def publish_crawl_tasks(self, links_to_crawl: List[LinkData]):
        link_count = 0

        for link in links_to_crawl:
            message = CrawlTask(
                url=link.url,
                scheduled_at=get_timestamp_eastern_time(),
                depth=link.depth
            )
            message.validate_publish()

            self._queue_service.publish(
                SchedulerQueueChannels.ADD_TO_QUEUE.value, message)
            link_count += 1

        self._logger.info("Published: %s Crawl Tasks", link_count)

from datetime import datetime
import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels, SchedulerLeakyBucket
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.schemas.link_processing_schemas import CacheSeenUrls, SaveProcessedLinks, SeenUrl
from shared.rabbitmq.queue_service import QueueService
from shared.utils import get_timestamp_eastern_time


# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    # TODO: Implement retry mechanism and dead-letter
    def publish_urls_to_schedule(self, page_links: ProcessDiscoveredLinks):
        BASE_INTERVAL_MS = 30  # for ~33 URLs/sec

        for i, link in enumerate(page_links.links):
            ttl = BASE_INTERVAL_MS * (i + 1)  # staggered TTLs
            link.validate_publish()

            # self._logger.debug("Publishing to delay queue: %s", link.url)

            self._queue_service.publish_with_ttl(
                queue_name=SchedulerLeakyBucket.LEAKY_BUCKET.value,
                message=link,
                ttl_ms=ttl
            )

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
            SchedulerQueueChannels.SEEN_LINKS_TO_CACHE.value, message)

        # self._logger.info("Published: Cache Processed Links")

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_processed_links(self, links_to_save: List[LinkData]):
        message = SaveProcessedLinks(links=links_to_save)
        message.validate_publish()

        self._queue_service.publish(
            SchedulerQueueChannels.SCHEDULED_LINKS_TO_SAVE.value, message)

        # self._logger.info("Published: Save Processed Links")

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
                SchedulerQueueChannels.URLS_TO_CRAWL.value, message)
            link_count += 1

        # self._logger.info("Published: %s Crawl Tasks", link_count)

import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels, DelayQueues
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.schemas.scheduling import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.schemas.save_to_db import SaveProcessedLinks, SaveLinksToSchedule
from shared.rabbitmq.queue_service import QueueService
from shared.utils import get_timestamp_eastern_time


# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    def publish_links_to_delay_queue(self, page_links: ProcessDiscoveredLinks):
        # BASE_INTERVAL_MS = 1000  # for ~33 URLs/sec

        # for i, link in enumerate(page_links.links):
        # ttl = BASE_INTERVAL_MS * (i + 1)  # staggered TTLs
        message = page_links
        message.validate_publish()

        # self._logger.debug("Publishing to delay queue: %s", page_links.links)

        self._queue_service.publish_with_ttl(
            queue_name=DelayQueues.SCHEDULER_DELAY_30MS.value,
            message=message,
            ttl_ms=1000
        )

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_processed_links(self, links_to_save: List[LinkData]):
        message = SaveProcessedLinks(links=links_to_save)

        self._queue_service.publish(
            SchedulerQueueChannels.SCHEDULED_LINKS_TO_SAVE.value, 
            message.model_dump_json())

        self._logger.info("Published: Save Processed Links")

    # TODO: Implement retry mechanism and dead-letter
    def publish_links_to_schedule(self, links_to_crawl: List[LinkData]):
        link_count = 0
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
        
        # link_count += 1

        self._logger.info("Published: %s Links Scheduled", len(scheduled_links))

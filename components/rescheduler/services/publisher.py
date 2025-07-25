import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.schemas.scheduling import LinkData
from shared.rabbitmq.schemas.save_to_db import SaveLinksToSchedule
from shared.utils import get_timestamp_eastern_time


# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    def publish_links_to_schedule(self, links_to_crawl: List[LinkData]):
        link_count = 0
        scheduled_links = []
        for link in links_to_crawl:
            task = CrawlTask(
                url=link.url,
                scheduled_at=get_timestamp_eastern_time(),
                depth=1
            )

            scheduled_links.append(task)
            link_count += 1
        message = SaveLinksToSchedule(links=scheduled_links)

        self._queue_service.publish(
            SchedulerQueueChannels.ADD_LINKS_TO_SCHEDULE.value, message.model_dump_json())
        self._logger.info("Published: %d links to schedule", link_count)

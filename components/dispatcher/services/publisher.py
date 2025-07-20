import logging
from typing import List
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.queue_service import QueueService


# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    def publish_crawl_tasks(self, links_to_crawl: List[CrawlTask]):
        link_count = 0
        # self._logger.info("Publishing links to crawl: %s", links_to_crawl)

        for link in links_to_crawl:
            message = link

            self._queue_service.publish(
                SchedulerQueueChannels.URLS_TO_CRAWL.value, message.model_dump_json())
            link_count += 1

        # self._logger.info("Published: %s Links To Crawl", link_count)

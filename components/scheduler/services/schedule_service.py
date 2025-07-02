
import logging
from typing import List
from shared.rabbitmq.schemas.crawling_task_schemas import SuccessCrawlReport
from shared.redis.cache_service import CacheService
from components.parser.configs.types import LinkData
from components.scheduler.message_handler import QueueService


class ScheduleService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        # redis setup
        self.cache = CacheService(self._logger)

        self._logger.info('Schedule Service Initiation Completed')

    def process_links(self, page_links: List[LinkData]):
        self._logger.info('STAGE 1 - Handle Duplicates')

        pass

    def handle_crawler_success_report(self, report: SuccessCrawlReport):

        pass

    def produce_crawl_task(self):
        pass

    def produce_store_links_task(self):
        pass

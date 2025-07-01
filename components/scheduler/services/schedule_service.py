
import logging
from typing import List
from cache_service import CacheService
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

    def handle_crawler_result(self):
        pass

    def _produce_crawl_task(self):
        pass

    def _produce_store_links_task(self):
        pass

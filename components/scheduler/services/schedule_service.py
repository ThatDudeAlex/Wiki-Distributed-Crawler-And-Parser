
import logging
from shared.rabbitmq.types import ProcessDiscoveredLinks
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService


class ScheduleService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        # redis setup
        self.cache = CacheService(self._logger)

        self._logger.info('Schedule Service Initiation Completed')

    # TODO: Scheduler - Implement
    def process_links(self, page_links: ProcessDiscoveredLinks):
        self._logger.info('STAGE 1 - Handle Duplicates & Filter')
        self._logger.info('SCHEDULER!!!!!!!')
        pass

    # TODO: Scheduler - Potentially better if pulled to a separate file in core/
    def _produce_crawl_task(self):
        pass

    def _produce_store_links_task(self):
        pass

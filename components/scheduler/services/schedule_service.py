
import logging
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService
from components.scheduler.core.filter import is_filtered


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
        length = len(page_links.links)
        valid_links = []
        self._logger.info('Link Processing Initiating....')

        for idx, link in enumerate(page_links.links, start=1):
            self._logger.debug(f'Processing link {idx}/{length} - {link.url}')

            # 1. Check For Duplicates
            if self.cache.is_in_seen:
                self._logger.debug(f'Discarding Duplicate URL - {link.url}')
                continue

            # 2. Apply Filter Rules
            if is_filtered(link):
                self._logger.debug(f'Filters Failed By - {link.url}')
                continue

            # 3. Add to 'seen' set
            self.cache.add_to_seen_set(link.url)

            # 4. Add to list of list to queue
            valid_links.append(link)

    def _produce_crawl_task(self):
        pass

    def _produce_store_links_task(self):
        pass

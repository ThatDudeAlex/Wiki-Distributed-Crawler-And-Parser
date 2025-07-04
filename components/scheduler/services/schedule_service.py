import logging
import time
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService
from components.scheduler.core.filter import is_filtered
from components.scheduler.services.publisher import PublishingService


class ScheduleService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._logger = logger
        self._queue_service = queue_service
        self.cache = CacheService(self._logger)
        self._publisher = PublishingService(self._queue_service, self._logger)

        self._logger.info("Schedule Service Initiation Completed")

    def process_links(self, page_links: ProcessDiscoveredLinks):
        total_links = len(page_links.links)
        valid_links = []

        self._logger.info(
            "Link Processing Initiated — %d links received", total_links)

        start_time = time.perf_counter()

        for idx, link in enumerate(page_links.links, start=1):
            self._logger.info("Processing link %d/%d - %s",
                              idx, total_links, link.url)

            # 1. Check For Duplicates
            if self.cache.is_in_seen(link.url):
                self._logger.info(
                    "Discarding link %d: Duplicate URL - %s", idx, link.url)
                continue

            # 2. Apply Filter Rules
            if is_filtered(link, self._logger):
                self._logger.info("Link %d: Filtered Out - %s", idx, link.url)
                continue

            # 3. Add to 'seen' set
            self.cache.add_to_seen_set(link.url)
            self._logger.debug("Link %d added to seen set - %s", idx, link.url)

            # 4. Add to list of valid links
            valid_links.append(link)
            self._logger.debug("Link %d appended to valid links", idx)

        elapsed = time.perf_counter() - start_time
        self._logger.info(
            "Link Processing Completed — %d links processed in %.2f seconds",
            total_links, elapsed
        )

        if not valid_links:
            self._logger.info(
                "No valid links found after filtering — skipping publish.")
            return

        self._logger.info("Publishing %d valid links", len(valid_links))
        self._publisher.publish_save_parsed_data(valid_links)
        self._publisher.publish_crawl_tasks(valid_links)

import logging
from typing import List, Optional
from components.scheduler.monitoring.metrics import (
    SCHEDULER_LINKS_DEDUPLICATED_TOTAL,
    SCHEDULER_LINKS_RECEIVED_TOTAL,
    SCHEDULER_LINKS_SCHEDULED_TOTAL,
    SCHEDULER_PROCESSING_DURATION_SECONDS,

)
from shared.rabbitmq.schemas.scheduling import ProcessDiscoveredLinks
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService
from components.scheduler.core.filter import FilteringService, LinkData
from components.scheduler.services.publisher import PublishingService
from concurrent.futures import ThreadPoolExecutor, as_completed


class ScheduleService:
    """
    Service responsible for processing discovered links before they are scheduled for crawling

    Includes:
        - Redis-based deduplication
        - Filtering (depth, domain, prefix, robots.txt)
        - Parallel processing for performance
        - Publishing to downstream queues
    """
    
    # TODO: remove docstrings from all __init__ methods
    def __init__(self, component_configs, redis_configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = component_configs
        self._logger = logger
        self._queue_service = queue_service
        self.cache = CacheService(redis_configs, logger)
        self._publisher = PublishingService(queue_service, logger)
        self.filter = FilteringService(component_configs, logger)

        self._logger.debug("Scheduler service initialized.")


    def process_links(self, page_links: ProcessDiscoveredLinks)  -> None:
        """
        Orchestrates processing of discovered links from a parsed page

        Filters out invalid or duplicate links, deduplicates via Redis, and
        publishes valid links to downstream services

        Args:
            page_links (ProcessDiscoveredLinks): All links discovered on a page awaiting processing
        """
        total_links = len(page_links.links)
        SCHEDULER_LINKS_RECEIVED_TOTAL.inc(total_links)
        

        with SCHEDULER_PROCESSING_DURATION_SECONDS.time():
            unseen_links = self._get_unseen_links(page_links.links)
            valid_links = self._process_links_concurrently(unseen_links)

        self._logger.info("Link Processing Completed — %d valid out of %d",
                      len(valid_links), total_links)


        if not valid_links:
            self._logger.info("No valid links found — skipping publish")
            return

        self._publish_valid_links(valid_links)

    def _get_unseen_links(self, all_links: List[LinkData]) -> List[LinkData]:
        all_urls = [link.url for link in all_links]

        try:
            seen_flags = self.cache.batch_is_seen_url(all_urls)
            unseen_links = [link for link, seen in zip(all_links, seen_flags) if not seen]

            deduplicated_count = len(all_links) - len(unseen_links)

            # Increment the metric by however many URLs were dropped because they had already
            # been processed before
            SCHEDULER_LINKS_DEDUPLICATED_TOTAL.inc(deduplicated_count)

            return unseen_links
        
        except Exception:
            self._logger.exception("Redis batch seen check failed")
            return all_links  # fail-safe

    def _process_single_link(self, link: LinkData, idx: int) -> Optional[LinkData]:
        try:
            if self.filter.is_filtered(link):
                return None
            if not self.cache.add_to_seen_set(link.url):
                return None
            return link
        
        except Exception:
            self._logger.exception("Error processing link %d (%s)", idx, link.url)
            return None

    def _process_links_concurrently(self, links: List[LinkData]) -> List[LinkData]:
        valid_links = []

        with ThreadPoolExecutor(max_workers=self.configs['max_workers']) as executor:
            futures = [
                executor.submit(self._process_single_link, link, idx)
                for idx, link in enumerate(links, start=1)
            ]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    valid_links.append(result)
                    
        return valid_links

    def _publish_valid_links(self, links: List[LinkData]) -> None:
        self._logger.info("Publishing %d valid links", len(links))
        SCHEDULER_LINKS_SCHEDULED_TOTAL.inc(len(links))
        self._publisher.publish_save_processed_links(links)
        self._publisher.publish_links_to_schedule(links)
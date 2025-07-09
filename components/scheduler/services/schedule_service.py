import logging
import time
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService
from components.scheduler.core.filter import FilteringService, LinkData
from components.scheduler.services.publisher import PublishingService
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 50


class ScheduleService:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._logger = logger
        self._queue_service = queue_service
        self.cache = CacheService(logger)
        self._publisher = PublishingService(queue_service, logger)
        self.filter = FilteringService(configs, logger)

        self._logger.info("Schedule Service Initiation Completed")

    def schedule_links(self, page_links: ProcessDiscoveredLinks):
        self._publisher.publish_links_to_delay_queue(page_links)

    def process_links(self, page_links: ProcessDiscoveredLinks):
        total_links = len(page_links.links)
        # quick and dirty way to get some metrics on what the link processing is doing
        # TODO: If keeping this, move it into it's own proper dataclass
        metric_counts = {
            'redi_add': 0,
            'duplicates': 0,
            'filtered': 0,
            'db_reader_cache_calls': 0,
            'db_reader_cache_success': 0,
            'db_reader_cache_fail': 0,
            'batch_seen_hits': 0,
            'batch_seen_misses': 0
        }

        start_time = time.perf_counter()
        valid_links = []

        all_links = page_links.links
        all_urls = [link.url for link in all_links]

        # Batch check seen URLs using Redis
        try:
            seen_flags = self.cache.batch_is_seen_url(all_urls)
            unseen_links = [
                link for link, seen in zip(all_links, seen_flags) if not seen
            ]
            metric_counts['batch_seen_hits'] = seen_flags.count(True)
            metric_counts['batch_seen_misses'] = seen_flags.count(False)
        except Exception as e:
            self._logger.error("Redis batch seen check failed: %s", str(e))
            unseen_links = all_links  # Fail-safe

        def process_single_link(link: LinkData, idx: int):
            try:
                # 1. Filter noise
                if self.filter.is_filtered(link):
                    metric_counts['filtered'] += 1
                    return None

                # 2. Final dedup gate: atomic Redis set
                was_added = self.cache.add_to_seen_set(link.url)
                if not was_added:
                    metric_counts['duplicates'] += 1
                    return None
                metric_counts['redi_add'] += 1

                return link

            except Exception as e:
                self._logger.error(
                    "Error processing link %d (%s): %s", idx, link.url, str(e))
                return None

        # Run processing loop in parallel
        with ThreadPoolExecutor(max_workers=self.configs.max_workers) as executor:
            futures = [
                executor.submit(process_single_link, link, idx)
                for idx, link in enumerate(unseen_links, start=1)
            ]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    valid_links.append(result)

        elapsed = time.perf_counter() - start_time
        self._logger.info("Link Processing Completed — %d valid out of %d in %.2fs",
                          len(valid_links), total_links, elapsed)
        self._logger.info(f"Metrics: {metric_counts}")

        if not valid_links:
            self._logger.info("No valid links found — skipping publish.")
            return

        self._logger.info("Publishing %d valid links", len(valid_links))
        self._publisher.publish_save_processed_links(valid_links)
        # self._publisher.publish_links_to_schedule(valid_links)

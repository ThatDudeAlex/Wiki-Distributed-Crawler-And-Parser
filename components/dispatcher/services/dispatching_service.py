
from datetime import datetime
import logging
from time import sleep
import time
from components.dispatcher.types.config_types import DispatcherConfig
from components.dispatcher.services.db_client import DBReaderClient
from components.dispatcher.services.publisher import PublishingService
from shared.redis.cache_service import CacheService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.utils import get_timestamp_eastern_time


class Dispatcher:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self.logger = logger
        self._dbclient = DBReaderClient()
        self._publisher = PublishingService(self._queue_service, self.logger)
        self._cache = CacheService(logger)
        self._last_heartbeat_check = 0
        self._cached_healthy_count = 0

        if self._dbclient.tables_are_empty():
            self.seed_empty_queue()

    def run(self):
        """Main dispatcher loop — fetches links and emits crawl tasks at a controlled rate."""
        # self.logger.info("Dispatcher started")//
        while True:
            try:
                # TODO: analyze why the redis health check causes a performance drop
                # of messages sent (as is, it's not good enough to count as ready)
                # num_healthy = self._get_healthy_crawler_count()
                # links = self._dbclient.pop_links_from_schedule(num_healthy)
                links = self._dbclient.pop_links_from_schedule(
                    self.configs.dispatch_count)

                if links:
                    tasks = [
                        CrawlTask(
                            url=link['url'],
                            scheduled_at=datetime.fromisoformat(
                                link['scheduled_at']),
                            depth=link['depth']
                        )
                        for link in links
                    ]
                    self._publisher.publish_crawl_tasks(tasks)

                sleep(self.configs.dispatch_tick)
                # sleep(1)
            except Exception as e:
                self.logger.error(
                    "Dispatcher encountered an error: %s", str(e))

    def _get_healthy_crawler_count(self) -> int:
        if time.time() - self._last_heartbeat_check > 50:
            self.logger.info('=== Getting Healthy Crawlers ===')
            self._cached_healthy_count = self._cache.get_heartbeat_count(
                self.configs.heartbeat_key_pattern, self.configs.scan_count
            )
            self._last_heartbeat_check = time.time()
            self.logger.info('New Cache Check: %s', self._last_heartbeat_check)

        return self._cached_healthy_count

    def seed_empty_queue(self):
        self.logger.info("Seeding Crawl Queue")
        seed_links = []
        for link in self.configs.seed_urls:
            seed_links.append(CrawlTask(
                url=link,
                depth=0,
                scheduled_at=get_timestamp_eastern_time()
            ))
            self._publisher.publish_crawl_tasks(seed_links)

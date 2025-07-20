
from datetime import datetime
import logging
from time import sleep
import time
from components.rescheduler.services.db_client import DBReaderClient
from components.rescheduler.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.utils import get_timestamp_eastern_time


class Rescheduler:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self.logger = logger
        self._dbclient = DBReaderClient()
        self._publisher = PublishingService(self._queue_service, self.logger)

    def run(self):
        """Main rescheduler loop — fetches pages that need recrawling and adds them to the schedule"""
        while True:
            try:

                pages = self._dbclient.get_pages_need_rescheduling()

                if pages:
                    tasks = [
                        CrawlTask(
                            url=page['url'],
                            scheduled_at=get_timestamp_eastern_time(),
                            # TODO: either add a depth column to the page table or remove it
                            # from crawl task since its not needed anymore
                            depth=1
                        )
                        for page in pages
                    ]
                    self._publisher.publish_links_to_schedule(tasks)

                sleep(self.configs.dispatch_tick)
                # sleep(1)
            except Exception as e:
                self.logger.error(
                    "rescheduler encountered an error: %s", str(e))

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

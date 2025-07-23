
from datetime import datetime
import logging
from time import sleep
from components.dispatcher.services.db_client import DBReaderClient
from components.dispatcher.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.utils import get_timestamp_eastern_time


class Dispatcher:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self.logger = logger
        self._dbclient = DBReaderClient()
        self._publisher = PublishingService(self._queue_service, self.logger)

        if self._dbclient.tables_are_empty():
            self.seed_empty_queue()

    def run(self):
        """Main dispatcher loop — fetches links and emits crawl tasks at a controlled rate"""
        # self.logger.info("Dispatcher started")//
        while True:
            try:
                links = self._dbclient.pop_links_from_schedule(
                    self.configs['dispatch_count'])

                if links:
                    tasks = [
                        CrawlTask(
                            url=link['url'],
                            scheduled_at=link['scheduled_at'],
                            depth=link['depth']
                        )
                        for link in links
                    ]
                    self._publisher.publish_crawl_tasks(tasks)

                sleep(self.configs['dispatch_tick'])
            except Exception as e:
                self.logger.error(
                    "Dispatcher encountered an error: %s", str(e))

    def seed_empty_queue(self):
        self.logger.info("Seeding Crawl Queue")
        seed_links = []
        for link in self.configs['seed_urls']:
            seed_links.append(CrawlTask(
                url=link,
                depth=0,
                scheduled_at=get_timestamp_eastern_time(isoformat=True)
            ))
            self._publisher.publish_crawl_tasks(seed_links)

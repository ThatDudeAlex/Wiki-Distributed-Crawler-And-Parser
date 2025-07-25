
import logging
from time import sleep
from typing import Any
from components.dispatcher.services.db_client import DBReaderClient
from components.dispatcher.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.utils import get_timestamp_eastern_time


class Dispatcher:
    """
    Dispatcher service responsible for orchestrating crawl jobs

    It continuously polls the DB for scheduled links, converts them into CrawlTask
    objects, and publishes them to the crawl queue. It also seeds the queue with
    initial links if the database is empty on startup.
    """

    def __init__(
            self, configs: dict[str, Any], queue_service: QueueService, logger: logging.Logger
        ):
        """
        Initialize the Dispatcher

        Args:
            configs (dict): Component-specific configuration dictionary
            queue_service (QueueService): RabbitMQ queue publisher
            logger (logging.Logger): Logger instance
        """

        self.configs = configs
        self._queue_service = queue_service
        self._logger = logger
        self._dbclient = DBReaderClient(
            logger, 
            self.configs['db_reader_timeout_seconds'])
        self._publisher = PublishingService(queue_service, logger)

        if self._dbclient.tables_are_empty():
            self.seed_empty_queue()


    def run(self) -> None:
        """
        Main dispatcher loop — fetches links from db_reader and emits crawl tasks
        at a fixed interval defined in config
        """
        while True:
            self._dispatch()
            sleep(self.configs['dispatch_tick'])


    def _dispatch(self) -> None:
        """
        Perform one iteration of the dispatcher loop:
        Fetch scheduled links from DB, convert them to crawl tasks, and publish.
        """
        try:
            links = self._dbclient.pop_links_from_schedule(self.configs['dispatch_count'])

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

        except Exception:
            self._logger.exception("Dispatcher encountered an unexpected error")


    def seed_empty_queue(self) -> None:
        """
        Seed the crawl queue with a set of predefined seed URLs

        Called at startup if the database is initially empty
        """
        self._logger.info("Seeding Crawl Queue")
        seed_links = []

        for link in self.configs['seed_urls']:
            seed_links.append(CrawlTask(
                url=link,
                depth=0,
                scheduled_at=get_timestamp_eastern_time(isoformat=True)
            ))
        self._publisher.publish_crawl_tasks(seed_links)

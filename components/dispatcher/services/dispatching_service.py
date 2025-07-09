
from datetime import datetime
import logging
from time import sleep
from components.dispatcher.types.config_types import DispatcherConfig
from components.dispatcher.services.db_client import DBReaderClient
from components.dispatcher.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask


# TODO: Implement redis client for hearbeat check
class Dispatcher:
    def __init__(self, configs: DispatcherConfig, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self.logger = logger
        self._dbclient = DBReaderClient()
        self._publisher = PublishingService(self._queue_service, self.logger)

    def run(self):
        """Main dispatcher loop — fetches links and emits crawl tasks at a controlled rate."""
        self.logger.info("Dispatcher started")
        while True:
            try:
                # TODO: make dynamic with crawler heartbeat
                links = self._dbclient.pop_links_from_schedule(32)

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

                sleep(1)
            except Exception as e:
                self.logger.error(
                    "Dispatcher encountered an error: %s", str(e))
            finally:
                self.logger.info("Dispatcher shutting down cleanly.")

    # TODO: Implement to remove the rabbit_seeder (let dispatcher handle function)
    def seed_empty_queue(self):
        pass

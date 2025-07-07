from datetime import datetime
import logging
from time import sleep
from dotenv import load_dotenv

from components.scheduler.services.db_client import DBReaderClient
from components.scheduler.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask


class Dispatcher:
    def __init__(self, queue_service: QueueService, dbclient: DBReaderClient, publisher: PublishingService, logger: logging.Logger):
        load_dotenv()
        self._logger = logger
        self._queue_service = queue_service
        self._dbclient = dbclient
        self._publisher = publisher
        self._running = True  # control flag for safe shutdown

    def stop(self):
        """Signal the dispatcher to stop running"""
        self._running = False

    def run(self):
        """Main dispatcher loop — fetches links and emits crawl tasks at a controlled rate."""
        self._logger.info("Dispatcher started")
        try:
            # while self._running:
            links = self._dbclient.pop_links_from_schedule(5)

            if links:
                self._logger.info("========== Got Some Links ==========")
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

            sleep(3)
        except Exception as e:
            self._logger.error("Dispatcher encountered an error: %s", str(e))
        finally:
            self._logger.info("Dispatcher shutting down cleanly.")

import logging
from time import sleep
from components.rescheduler.services.db_client import DBReaderClient
from components.rescheduler.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.save_to_db import CrawlTask
from shared.utils import get_timestamp_eastern_time

from components.rescheduler.monitoring.metrics import (
    RESCHEDULER_PAGES_RESCHEDULED_TOTAL,
    RESCHEDULER_CRAWL_TASKS_PUBLISHED_TOTAL,
    RESCHEDULER_ERRORS_TOTAL,
    RESCHEDULER_RESCHEDULE_LATENCY_SECONDS,
)


class Rescheduler:
    """
    The Rescheduler component is responsible for periodically identifying pages 
    that require re-crawling and dispatching them as crawl tasks to the message queue.

    It periodically polls the DB for  pages due for rescheduling, converts them into CrawlTask
    objects, and publishes them to the crawl queue.
    """

    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self._logger = logger
        self._dbclient = DBReaderClient(
            logger,
            self.configs['db_reader_timeout_seconds']
        )
        self._publisher = PublishingService(self._queue_service, self._logger)


    def run(self) -> None:
        """
        Main rescheduling loop
        """
        while True:
            sleep(self.configs['rescheduling_tick'])
            self._logger.info("Rescheduler Running...")
            self._reschedule()


    def _reschedule(self) -> None:
        """
        Perform one iteration of the rescheduler loop
        """
        try:
            with RESCHEDULER_RESCHEDULE_LATENCY_SECONDS.time():
                pages = self._dbclient.get_pages_need_rescheduling()
                self._logger.info(pages)

                if pages:
                    RESCHEDULER_PAGES_RESCHEDULED_TOTAL.inc(len(pages))

                    tasks = [
                        CrawlTask(
                            url=page['url'],
                            depth=page['depth'],
                            scheduled_at=get_timestamp_eastern_time(isoformat=True),
                        )
                        for page in pages
                    ]
                    
                    self._publisher.publish_crawl_tasks(tasks)
                    
        except Exception:
            self._logger.exception("Rescheduler encountered an unexpected error")
            RESCHEDULER_ERRORS_TOTAL.inc()

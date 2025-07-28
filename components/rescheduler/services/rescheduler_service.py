
import logging
from time import sleep
from components.rescheduler.services.db_client import DBReaderClient
from components.rescheduler.services.publisher import PublishingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.save_to_db import CrawlTask
from shared.utils import get_timestamp_eastern_time


class Rescheduler:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs
        self._queue_service = queue_service
        self._logger = logger
        self._dbclient = DBReaderClient(
            logger,
            self.configs['db_reader_timeout_seconds'])
        self._publisher = PublishingService(self._queue_service, self._logger)


    def run(self) -> None:
        """
        Main rescheduling loop
        """
        while True:
            self._logger.info("Rescheuduler Running...")
            self._reschedule()
            sleep(self.configs['rescheduling_tick'])

    
    def _reschedule(self) -> None:
        """
        Perform one iteration of the rescheduler loop:
        """
        try:
            pages = self._dbclient.get_pages_need_rescheduling()
            self._logger.info(pages)

            if pages:
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
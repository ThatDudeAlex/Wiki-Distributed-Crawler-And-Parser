from datetime import datetime
import logging
from components.crawler.configs.types import FetchResponse
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlStatus, SuccessCrawlReport, FailedCrawlReport
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def publish_sucess_report(
            self,
            fetched_response: FetchResponse,
            url_hash: str,
            html_content_hash: str,
            compressed_filepath: str,
            fetched_at: str
    ):
        message = SuccessCrawlReport(
            url=fetched_response.url,
            status=fetched_response.crawl_status,
            http_status_code=fetched_response.status_code,
            url_hash=url_hash,
            html_content_hash=html_content_hash,
            compressed_filepath=compressed_filepath,
            fetched_at=fetched_at,
        ).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.REPORT.value, message)

        self._logger.info("Published: Crawl Report - Success")

    def publish_fail_report(
        self,
        url: str,
        status: CrawlStatus,
        fetched_at: datetime,
        error_type: str = None,
        error_message: str = None
    ):
        message = FailedCrawlReport(
            url=url, status=status, fetched_at=fetched_at,
            error_type=error_type, error_message=error_message
        ).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.REPORT.value, message)

        self._logger.info("Published: Crawl Report - Failed")

    def publish_parsing_task(self, url: str, compressed_filepath: str):
        message = ParsingTask(
            url=url, compressed_filepath=compressed_filepath).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.PARSE.value, message
        )
        self._logger.debug("Published: Parsing Task - %s", compressed_filepath)

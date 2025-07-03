from datetime import datetime
import logging
from components.crawler.configs.types import FetchResponse
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlStatus, PageMetadataMessage
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def store_successful_crawl(
            self,
            fetched_response: FetchResponse,
            url_hash: str,
            html_content_hash: str,
            compressed_filepath: str,
            fetched_at: str
    ):
        message = PageMetadataMessage(
            status=fetched_response.crawl_status,
            fetched_at=fetched_at,
            url=fetched_response.url,
            http_status_code=fetched_response.status_code,
            url_hash=url_hash,
            html_content_hash=html_content_hash,
            compressed_filepath=compressed_filepath,
        ).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.SAVE_CRAWL_DATA.value, message)

        self._logger.info("Published: Page Metadata - Success")

    def store_failed_crawl(
        self,
        status: CrawlStatus,
        fetched_at: datetime,
        url: str,
        error_type: str = None,
        error_message: str = None
    ):
        message = PageMetadataMessage(
            url=url, status=status, fetched_at=fetched_at,
            error_type=error_type, error_message=error_message
        ).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.SAVE_CRAWL_DATA.value, message)

        self._logger.info("Published: Page Metadata - Failed Crawl")

    def publish_parsing_task(self, url: str, depth: int, compressed_filepath: str):
        message = ParsingTask(
            url=url, depth=depth, compressed_filepath=compressed_filepath).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.PARSE.value, message
        )
        self._logger.debug("Published: Parsing Task - %s", compressed_filepath)

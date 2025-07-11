from datetime import datetime
import logging
from components.crawler.types.crawler_types import FetchResponse
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlStatus, SavePageMetadataTask, ValidationError
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def _publish_page_metadata(self, message: SavePageMetadataTask):
        try:
            message.validate_publish()

            self._queue_service.publish(
                CrawlerQueueChannels.PAGE_METADATA_TO_SAVE.value, message
            )

            if message.status == CrawlStatus.SUCCESS:
                self._logger.info("Published: Page Metadata - Success")
            else:
                self._logger.info("Published: Page Metadata - Failed Crawl")

        except ValidationError as e:
            self._logger.error("Validation failed: %s", str(e))

    def store_successful_crawl(
        self,
        fetched_response: FetchResponse,
        url_hash: str,
        html_content_hash: str,
        compressed_filepath: str,
        fetched_at: datetime,
        next_crawl: datetime
    ):
        page_metadata = SavePageMetadataTask(
            status=fetched_response.crawl_status,
            fetched_at=fetched_at,
            next_crawl=next_crawl,
            url=fetched_response.url,
            http_status_code=fetched_response.status_code,
            url_hash=url_hash,
            html_content_hash=html_content_hash,
            compressed_filepath=compressed_filepath,
        )
        self._publish_page_metadata(page_metadata)

    def store_failed_crawl(
        self,
        status: CrawlStatus,
        fetched_at: datetime,
        url: str,
        error_type: str = None,
        error_message: str = None
    ):
        page_metadata = SavePageMetadataTask(
            url=url,
            status=status,
            fetched_at=fetched_at,
            error_type=error_type,
            error_message=error_message
        )
        self._publish_page_metadata(page_metadata)

    def publish_parsing_task(self, url: str, depth: int, compressed_filepath: str):
        message = ParsingTask(
            url=url, depth=depth, compressed_filepath=compressed_filepath
        )
        # Validate Message
        message.validate_publish()

        # convert message to dict to so that it's JSON serializable
        self._queue_service.publish(
            CrawlerQueueChannels.PAGES_TO_PARSE.value, message)
        self._logger.debug(
            "Published: Parsing Task - %s", compressed_filepath
        )

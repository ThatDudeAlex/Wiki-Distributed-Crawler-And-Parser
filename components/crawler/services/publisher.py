from dataclasses import asdict
from datetime import datetime
import logging
from components.crawler.configs.types import FetchResponse
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlStatus, SavePageMetadataTask, ValidationError
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def _publish_page_metadata(self, page_metadata: SavePageMetadataTask):
        try:
            page_metadata.validate()
            message = asdict(page_metadata)

            self._queue_service.publish(
                CrawlerQueueChannels.SAVE_PAGE_DATA.value, message
            )

            if page_metadata.status == CrawlStatus.SUCCESS:
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
            fetched_at: str
    ):
        page_metadata = SavePageMetadataTask(
            status=fetched_response.crawl_status,
            fetched_at=fetched_at,
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
            url=url, depth=depth, compressed_filepath=compressed_filepath).model_dump_json()

        self._queue_service.publish(
            CrawlerQueueChannels.PARSE.value, message
        )
        self._logger.debug(
            "Published: Parsing Task - %s", compressed_filepath)

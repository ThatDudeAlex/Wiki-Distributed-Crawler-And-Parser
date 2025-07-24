import logging
from components.crawler.types.crawler_types import FetchResponse
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.rabbitmq.schemas.save_to_db import SavePageMetadataTask
from shared.rabbitmq.schemas.parsing import ParsingTask
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    """
    Responsible for publishing structured messages to RabbitMQ queues.

    Handles:
        - Page metadata storage (successful & failed crawls)
        - Parsing task dispatch
        - Logging publishing status
    """

    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger

    def _publish_page_metadata(self, message: SavePageMetadataTask):
        """
        Internal helper to publish page metadata to the `page_metadata_to_save` queue.

        Args:
            message (SavePageMetadataTask): Pydantic object containing crawl metadata.

        Raises:
            Logs error if publishing fails unexpectedly.
        """
        
        try:
            self._queue_service.publish(
                CrawlerQueueChannels.PAGE_METADATA_TO_SAVE.value, message.model_dump_json()
            )

            if message.status == CrawlStatus.SUCCESS:
                self._logger.info("Published: Page Metadata - Success")
            else:
                self._logger.info("Published: Page Metadata - Failed Crawl")

        except Exception as e:
            self._logger.error("Unexpected error occurred: %s", e)

    def store_successful_crawl(
        self,
        fetched_response: FetchResponse,
        url_hash: str,
        html_content_hash: str,
        compressed_filepath: str,
        fetched_at: str,
        next_crawl: str
    ):
        """
        Format and publish metadata for a successful crawl task.

        Args:
            fetched_response (FetchResponse): Response object from HTTP fetcher
            url_hash (str): SHA hash of the original URL
            html_content_hash (str): SHA hash of the downloaded HTML content
            compressed_filepath (str): Path of the compressed HTML file
            fetched_at (str): ISO timestamp when the crawl completed
            next_crawl (str): ISO timestamp for the next eligible crawl time
        """

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
        fetched_at: str,
        url: str,
        error_type: str = None,
        error_message: str = None
    ):
        """
        Format and publish metadata for a failed crawl task.

        Args:
            status (CrawlStatus): The reason/category for crawl failure
            fetched_at (str): Timestamp when the crawl attempt ended
            url (str): Original URL that failed
            error_type (str, optional): Error class name (e.g. TimeoutError)
            error_message (str, optional): Error message string
        """
        page_metadata = SavePageMetadataTask(
            url=url,
            status=status,
            fetched_at=fetched_at,
            error_type=error_type,
            error_message=error_message
        )
        self._publish_page_metadata(page_metadata)

    def publish_parsing_task(self, url: str, depth: int, compressed_filepath: str):
        """
        Publish a new task to the parsing queue for downstream processing.

        Args:
            url (str): Original URL of the page
            depth (int): Crawl depth used for prioritization/scope control
            compressed_filepath (str): Path to the compressed HTML file
        """
        try:
            message = ParsingTask(
                url=url, depth=depth, compressed_filepath=compressed_filepath
            )

            self._queue_service.publish(
                CrawlerQueueChannels.PAGES_TO_PARSE.value, message.model_dump_json())
            self._logger.debug(
                "Published: Parsing Task - %s", compressed_filepath
            )
        except Exception as e:
            self._logger.error("Failed to publish parsing task: %s", e)


import logging
import os

from dotenv import load_dotenv
from components.crawler.configs.types import FetchResponse
from components.crawler.services.downloader import download_compressed_html_content
from components.crawler.services.publisher import PublishingService
from components.crawler.core.crawler import crawl
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.utils import get_timestamp_eastern_time, create_hash


class CrawlerService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger, max_depth: int):

        # TODO: Use a config_service instead of using load_dotenv()
        load_dotenv()

        self.max_depth = max_depth

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        # queue publisher setup
        self.publisher = PublishingService(self.queue_service, self._logger)

        self._logger.info('Crawler Service Initiation Complete')

    def run(self, task: CrawlTask):
        # skip task if it exceeds the max depth
        if task.depth > self.max_depth:
            self._logger.info(
                f"Current Depth '{task.depth}' Exceeded Max Depth '{self.max_depth}' - Skipping '{task.url}'"
            )
            return

        self._logger.info('STAGE 1: Fetch URL: %s', task.url)
        fetched_response: FetchResponse = crawl(task.url, self._logger)

        # if crawl failed or was skipped due to robot.txt
        if not fetched_response.success:
            # Timestamp of when crawling finished
            fetched_at = get_timestamp_eastern_time()

            self.publisher.store_failed_crawl(
                task.url, fetched_response.crawl_status, fetched_at,
                fetched_response.error_type, fetched_response.error_message)
            return

        # TODO: Implement try/catch with retry for download
        self._logger.info('STAGE 2: Create Hash of Html file')
        html_content_hash = create_hash(fetched_response.text)

        self._logger.info('STAGE 3: Download Compressed Html File')
        url_hash, compressed_filepath = download_compressed_html_content(
            os.getenv('DL_HTML_PATH'), task.url, fetched_response.text, self._logger)

        # Timestamp of when crawling finished
        fetched_at = get_timestamp_eastern_time()

        self._logger.info(
            'STAGE 4: Publish Page Metadata Report')
        self.publisher.store_successful_crawl(
            fetched_response, url_hash, html_content_hash, compressed_filepath, fetched_at)

        self._logger.info('STAGE 5: Tell Parsers to extract page content')
        self.publisher.publish_parsing_task(
            task.url, task.depth, compressed_filepath)

        self._logger.info('Crawl Task Successfully Completed!')

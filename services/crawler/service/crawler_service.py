
import logging
import os

from dotenv import load_dotenv
from pydantic import FilePath
from services.crawler.domain.types import CrawlerResponse, FailedCrawlTask, ParseDonwloadedPageTask, SavePageTask
from services.crawler.infrastructure.download_handler import download_compressed_html_content
from services.crawler.domain.crawler import crawl
from shared.queue_service import QueueService
from shared.config import CRAWLER_QUEUE_CHANNELS
from shared.utils import get_timestamp_eastern_time


class CrawlerService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger, max_depth: int):
        load_dotenv()
        self.max_depth = max_depth

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        # TODO: Remove if redis is no longer needed here
        # redis setup
        # self.cache = CacheService(self._logger)

        self._logger.info('Crawler Service Initiation Complete')

    def run(self, url: str, depth: int):
        # skip task if it exceeds the max depth
        if depth > self.max_depth:
            self._logger.debug(
                f"Current Depth '{depth}' Exceeded Max Depth '{self.max_depth}' - Skipping '{url}'"
            )
            return

        crawler_response: CrawlerResponse = crawl(url)

        # if crawl failed or was skipped due to robot.txt
        if not crawler_response.success:
            self._publish_failed_crawl(crawler_response)
            return

        # download compressed html file
        url_hash, compressed_path = download_compressed_html_content(
            os.getenv('DL_HTML_PATH'), url, crawler_response.data.text, self._logger)

        # get timestamp of when crawling finished
        crawl_time = get_timestamp_eastern_time()

        # publish message to store page into db
        self._publish_save_page(
            crawler_response, url_hash, compressed_path, crawl_time
        )

        # publish message to begin a parsing task for the downloaded page
        self._publish_parse_downloaded_page(url, compressed_path)

    def _publish_failed_crawl(self, crawler_response: CrawlerResponse):
        message = FailedCrawlTask(
            url=crawler_response.url,
            crawl_status=crawler_response.crawl_status,
            status_code=None if not crawler_response.data else crawler_response.data.status_code,
            error_message=crawler_response.error['message']
        )
        self.queue_service.publish(
            CRAWLER_QUEUE_CHANNELS['failed'], message.model_dump()
        )
        self._logger.debug(
            f"Published - Failed Task: {message.model_dump_json()}"
        )

    def _publish_save_page(
            self,
            crawler_response: CrawlerResponse,
            url_hash: str,
            compressed_path: FilePath,
            crawl_time: str
    ):
        message = SavePageTask(
            url=crawler_response.url,
            url_hash=url_hash,
            crawl_status=crawler_response.crawl_status,
            compressed_path=compressed_path,
            crawl_time=crawl_time,
            status_code=crawler_response.data.status_code
        )
        self.queue_service.publish(
            CRAWLER_QUEUE_CHANNELS['savepage'], message.model_dump()
        )
        self._logger.debug(
            f"Published - Save Page Task: {message.model_dump_json()}"
        )

    def _publish_parse_downloaded_page(self, url: str, compressed_path: FilePath):
        message = ParseDonwloadedPageTask(
            url=url,
            compressed_path=compressed_path
        )
        self.queue_service.publish(
            CRAWLER_QUEUE_CHANNELS['parsetask'], message.model_dump()
        )
        self._logger.debug(
            f"Published - Parse Downloaded Page Task: {message.model_dump_json()}"
        )

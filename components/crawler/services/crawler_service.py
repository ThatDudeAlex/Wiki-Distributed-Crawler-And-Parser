
import logging
import os

from dotenv import load_dotenv
from components.crawler.configs.types import CrawlerResponse
from components.crawler.services.downloader import download_compressed_html_content
from components.crawler.core.crawler import crawl
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import SuccessCrawlReport, FailedCrawlReport
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.utils import get_timestamp_eastern_time


class CrawlerService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger, max_depth: int):

        # TODO: Use a config_service instead of using load_dotenv()
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
            self._logger.info(
                f"Current Depth '{depth}' Exceeded Max Depth '{self.max_depth}' - Skipping '{url}'"
            )
            return

        self._logger.info('STAGE 1: Fetch URL: %s', url)
        crawler_response: CrawlerResponse = crawl(url, self._logger)

        # if crawl failed or was skipped due to robot.txt
        if not crawler_response.success:
            self._send_failed_report_message(crawler_response)
            return

        # TODO: Implement try/catch with retry for download
        self._logger.info('STAGE 2: Download Compressed Html File')

        url_hash, compressed_path = download_compressed_html_content(
            os.getenv('DL_HTML_PATH'), url, crawler_response.data.text, self._logger)

        # get timestamp of when crawling finished
        crawl_time = get_timestamp_eastern_time()

        self._logger.info('STAGE 3: Tell DB_Service to store the page data')

        self._send_sucess_report_message(
            crawler_response, url_hash, compressed_path, crawl_time
        )

        self._logger.info('STAGE 4: Tell Parsers to extract page content')

        self._publish_parse_downloaded_page(url, compressed_path)

        self._logger.info('Crawl Task Successfully Completed!')

    def _send_failed_report_message(self, crawler_response: CrawlerResponse):
        message = {
            "url": crawler_response.url,
            "crawl_status": crawler_response.crawl_status,
            "status_code": crawler_response.data.status_code if crawler_response.data else None,
            "error_message": crawler_response.error["message"] if crawler_response.error else None
        }
        self.queue_service.publish(CrawlerQueueChannels.REPORT.value, message)
        self._logger.debug(f"Task Published - Save Failed Crawl: {message}")

    # TODO: Implement retry mechanism and dead-letter
    def _send_sucess_report_message(
            self,
            crawler_response: CrawlerResponse,
            url_hash: str,
            compressed_path: str,
            crawl_time: str
    ):
        message = SuccessCrawlReport(
            url=crawler_response.url,
            url_hash=url_hash,
            crawl_status=crawler_response.crawl_status,
            compressed_path=compressed_path,
            crawl_time=crawl_time,
            status_code=crawler_response.data.status_code if crawler_response.data else None
        ).model_dump_json()
        # message = {
        #     "url": crawler_response.url,
        #     "url_hash": url_hash,
        #     "crawl_status": crawler_response.crawl_status.value,
        #     "compressed_path": compressed_path,
        #     "crawl_time": crawl_time,
        #     "status_code": crawler_response.data.status_code
        # }
        self.queue_service.publish(
            CrawlerQueueChannels.REPORT.value, message)
        self._logger.debug(
            f"Task Published - Save Successful Crawl: {message}")

    def _publish_parse_downloaded_page(self, url: str, compressed_path: str):
        message = {
            "url": str(url),
            "compressed_path": compressed_path
        }
        self.queue_service.publish(
            CrawlerQueueChannels.PARSE.value, message
        )
        self._logger.debug(f"Task Published - Parse Html Content: {message}")

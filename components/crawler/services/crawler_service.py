
from datetime import timedelta
import logging
import time

from components.crawler.types.crawler_types import FetchResponse
from components.crawler.services.downloader import download_compressed_html_content
from components.crawler.services.publisher import PublishingService
from components.crawler.core.crawler import crawl
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.utils import get_timestamp_eastern_time, create_hash

# Assuming metrics.py in the same directory
from components.crawler.core.metrics import CRAWL_PAGES_TOTAL, CRAWL_PAGES_FAILURES_TOTAL, PAGE_CRAWL_LATENCY_SECONDS


class CrawlerService:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self.configs = configs

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        # TODO: Remove if hearbeat is no longer going to be use
        # setup hearbeat (simple component health-check)
        # self.heartbeat = HeartBeat(configs, logger)
        # self._last_heartbeat_post = time.time()

        # queue publisher setup
        self.publisher = PublishingService(self.queue_service, self._logger)

        self._logger.info('Crawler Service Initiation Complete')

    def run(self, task: CrawlTask):
        url = task.url
        depth = task.depth

        # Default status (for crawler_service_crawl_tasks_total metric)
        task_status = CrawlStatus.SUCCESS.value

        # Start timer for measuring overall crawl time
        start_time = time.time()

        try:
            self._logger.info('STAGE 1: Fetch URL: %s', url)
            fetched_response: FetchResponse = crawl(url, self._logger)

            # if crawl failed
            if not fetched_response.success:
                # Timestamp of when crawling finished
                fetched_at = get_timestamp_eastern_time()

                self.publisher.store_failed_crawl(
                    url, fetched_response.crawl_status, fetched_at,
                    fetched_response.error_type, fetched_response.error_message)

                # Increment failure counter
                self._increment_failed_counter(
                    fetched_response.error_type, fetched_response.crawl_status.value
                )
                task_status = CrawlStatus.FAILED.value
                return

            html_content = fetched_response.text

            # TODO: Implement try/catch with retry for download
            self._logger.info('STAGE 2: Create Hash of Html file')
            html_content_hash = create_hash(html_content)

            self._logger.info('STAGE 3: Download Compressed Html File')
            url_hash, filepath = download_compressed_html_content(
                self.configs['storage_path'], url, html_content, self._logger)

            # Timestamp of when crawling finished + next scheduled crawl
            fetched_at = get_timestamp_eastern_time()
            next_crawl = (
                fetched_at + timedelta(seconds=self.configs['recrawl_interval'])
            )

            self._logger.info('STAGE 4: Publish Page Metadata Report')
            self.publisher.store_successful_crawl(
                fetched_response, url_hash, html_content_hash, filepath, fetched_at, next_crawl)

            self._logger.info('STAGE 5: Tell Parsers to extract page content')
            self.publisher.publish_parsing_task(url, depth, filepath)

            self._logger.info('Crawl Task Successfully Completed!')

        except Exception as e:
            self._logger.error(
                f"Unexpected error during crawl task for {url}: {e}")
            self._increment_failed_counter(
                type(e).__name__, CrawlStatus.FAILED.value
            )
            task_status = CrawlStatus.FAILED.value

        # Finally is NEEDED to increase CRAWL_PAGES_TOTAL counter & record crawl time
        finally:
            latency = time.time() - start_time
            CRAWL_PAGES_TOTAL.labels(status=task_status).inc()
            self._record_latency(task_status, latency)

    def _increment_failed_counter(self, error_type: str, crawl_status: str) -> None:
        CRAWL_PAGES_FAILURES_TOTAL.labels(
            error_type=error_type, crawl_status=crawl_status).inc()

    def _increment_page_crawl_counter(self, task_status: str) -> None:
        CRAWL_PAGES_TOTAL.labels(status=task_status).inc()

    def _record_latency(self, task_status: str, latency: int) -> None:
        PAGE_CRAWL_LATENCY_SECONDS.labels(
            status=task_status).observe(latency)

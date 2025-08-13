
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from components.crawler.services.publisher import PublishingService
from components.crawler.core.downloader import download_compressed_html_content
from components.crawler.core.http_fetcher import HttpFetcher
from components.crawler.types.crawler_types import FetchResponse
from components.crawler.monitoring.metrics import (
    CRAWL_PAGES_TOTAL, CRAWL_PAGES_FAILURES_TOTAL, 
    CRAWLER_HTML_DOWNLOAD_RETRIES_TOTAL, PAGE_CRAWL_LATENCY_SECONDS
)
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.enums.crawl_status import CrawlStatus
from shared.utils import get_timestamp_eastern_time, create_hash
from urllib.parse import urlparse


class CrawlerService:
    """
    Core crawler orchestration class.

    Responsible for executing a full crawl task lifecycle:
        - Fetching page HTML
        - Compressing & storing content
        - Recording crawl metadata
        - Publishing page for downstream parsing
        - Emitting Prometheus metrics
    """

    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        """
        Initializes the CrawlerService

        Args:
            configs (dict): Configuration dictionary for crawlers
            queue_service (QueueService): RabbitMQ interface for publishing results
            logger (logging.Logger): Logger instance
        """
        self.configs = configs

        # logger setup
        self._logger = logger

        # queue setup
        self.queue_service = queue_service

        self.http_fetcher = HttpFetcher(configs, logger)

        # queue publisher setup
        self.publisher = PublishingService(queue_service, logger)

        self._logger.info('Crawler Service Initiation Complete')

    def run(self, task: CrawlTask):
        """
        Run the full crawl lifecycle for a given CrawlTask

        Args:
            task (CrawlTask): Contains URL, depth, and metadata for the crawl job

        Flow:
            1. Fetch the page via HTTP
            2. Save the raw HTML to disk (compressed)
            3. Generate hashes & metadata
            4. Publish metadata and downstream parse job
            5. Record Prometheus metrics
        """
        url, depth = task.url, task.depth

        # Default status (for crawl_pages_total metric)
        task_status = CrawlStatus.SUCCESS.value

        # Start timer for measuring overall crawl time
        start_time = time.time()

        try:
            self._logger.info('STAGE 1: Fetch URL: %s', url)
            fetched_response = self._fetch_page(url)

            # If fetch failed, move on
            if not fetched_response:
                task_status = CrawlStatus.FAILED.value
                return

            html_content = fetched_response.text

            self._logger.info('STAGE 2: Download Compressed Html File')
            url_hash, filepath = self._download_compressed_html(url, html_content)

            self._logger.info('STAGE 3: Create Hash of Html file')
            html_content_hash = create_hash(html_content)

            # Timestamp of when crawling finished + next scheduled crawl
            fetched_at, next_crawl = self._get_crawl_timestamps_isoformat()

            self._logger.info('STAGE 4: Publish Page Metadata Report')
            self.publisher.store_successful_crawl(
                fetched_response, url_hash, html_content_hash, filepath, fetched_at, next_crawl)

            self._logger.info('STAGE 5: Tell Parsers to extract page content')
            self.publisher.publish_parsing_task(url, depth, filepath)

            self._logger.info('Crawl Task Successfully Completed!')

        except Exception as e:
            self._logger.error(f"Unexpected error during crawl task for {url}: {e}")
            task_status = CrawlStatus.FAILED.value
            CRAWL_PAGES_FAILURES_TOTAL.labels(
                error_type=type(e).__name__, 
                crawl_status=task_status
            ).inc()
           
        # Finally is NEEDED to increase CRAWL_PAGES_TOTAL counter & record crawl time
        finally:
            latency = time.time() - start_time
            PAGE_CRAWL_LATENCY_SECONDS.labels(status=task_status).observe(latency)
            CRAWL_PAGES_TOTAL.labels(status=task_status).inc()

    def _fetch_page(self, url) -> Optional[FetchResponse]:
        """
        Fetch the HTML content of the given URL using the HttpFetcher

        If the fetch fails:
            - Publishes failure info to queue
            - Logs & increments Prometheus failure counter

        Returns:
            FetchResponse if successful, else None
        """
        fetched_response = self.http_fetcher.crawl_url(url)

        # if crawl failed
        if not fetched_response.success:
            self._logger.warning(f"Crawl failed for URL: {url}")

            # Timestamp of when crawling finished
            fetched_at = get_timestamp_eastern_time()

            self.publisher.store_failed_crawl(
                fetched_response.crawl_status, fetched_at, url,
                fetched_response.error_type, fetched_response.error_message)

            # Increment failure counter
            CRAWL_PAGES_FAILURES_TOTAL.labels(
                error_type= fetched_response.error_type,
                crawl_status=fetched_response.crawl_status.value
            ).inc()

            return None

        return fetched_response
    
    def _download_compressed_html(self, url, html) -> Tuple[str, str]:
        """
        Attempt to compress and save the HTML content to disk, with retry

        Args:
            url (str): Page URL (used for hash-based filename)
            html (str): Raw HTML content

        Returns:
            tuple[str, str]: (hash of URL, path to .gz file)

        Raises:
            OSError: If saving fails after configured retries
        """
        attempt = 0
        retries = self.configs['download_retry']['attempts']
        grace_period = self.configs['download_retry']['grace_period_seconds']

        while attempt <= retries:
            try:
                return download_compressed_html_content(self.configs['storage_path'], url, html, self._logger)
            except OSError as e:
                self._logger.warning(f"[RETRY] HTML download failed ({attempt+1}/{retries+1}) for {url}: {e}")

                if attempt > 0:
                    parsed_host = urlparse(url).netloc or "unknown"
                    CRAWLER_HTML_DOWNLOAD_RETRIES_TOTAL.labels(url_host=parsed_host).inc()

                if attempt == retries:
                    self._logger.error(f"[GIVEUP] Could not download HTML after {retries+1} attempts")
                    raise
                
                attempt += 1
                time.sleep(grace_period)

    def _get_crawl_timestamps_isoformat(self) -> tuple[str, str]:
        """
        Compute the current crawl timestamp and next crawl eligibility time

        Returns:
            tuple(str, str): (current ISO timestamp, next eligible crawl ISO timestamp)
        """
        recrawl_interval = self.configs['recrawl_interval']

        # Timestamp of when crawling finished + next scheduled crawl
        fetched_at = get_timestamp_eastern_time(isoformat=True)

        next_crawl = (
            datetime.fromisoformat(fetched_at) + timedelta(seconds=recrawl_interval)
        ).isoformat()

        return fetched_at, next_crawl

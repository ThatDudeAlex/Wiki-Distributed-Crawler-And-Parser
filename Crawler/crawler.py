
import os
import json
from .cache_service import CacheService
from .robot_hander import RobotHandler
from .download_handler import DownloadHandler
from .fetcher import Fetcher
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from database.db_models.models import CrawlStatus
from shared import utils
from shared.queue_service import QueueService
from shared.db_service import DatabaseService
from shared.logger import setup_logging
from shared.config import (
    SEED_URL, BASE_HEADERS, MAX_DEPTH, CRAWL_QNAME, PARSE_QNAME)


class WebCrawler:
    def __init__(self):
        load_dotenv()
        self._logger = setup_logging(
            os.getenv('CRAWL_LOGS', 'logs/crawler.log')
        )

        # rabbitMQ setup
        self.queue = QueueService(CRAWL_QNAME, PARSE_QNAME, self._logger)
        self.queue.channel.basic_consume(
            queue=CRAWL_QNAME,
            on_message_callback=self._consume_rabbit_message,
            auto_ack=False
        )

        # redis setup
        self.cache = CacheService(self._logger)

        # robot.txt setup
        self.robot = RobotHandler(self._logger)

        # html downloader setup
        self.downloader = DownloadHandler(self._logger)

        # http fetcher setup
        self.fetcher = Fetcher(self._logger, BASE_HEADERS)

        # database setup
        self.db = DatabaseService(self._logger)

        # TODO: move into the database
        # self.count = 0  # number of urls navigated to
        # self.skipped = 0  # number of urls skipped

        # Only becomes true if it doesnt exist - This helps prevent the race condition of
        # multiple instances & allows only 1 instance to make the seed the queue
        queue_is_seeded = self.cache.set_if_not_existing(SEED_URL)

        if queue_is_seeded:
            self.cache.add_to_enqueued_set(SEED_URL)
            self._add_to_crawl_queue((SEED_URL, 0))

        self._logger.info('Crawler Initiation Complete')

    """" === RabiitMQ Methods === """

    def _add_to_crawl_queue(self, payload):
        try:
            self.queue.publish(CRAWL_QNAME, payload)
        except Exception as e:
            self._logger.error(f"Issue adding to the crawler queue: {e}")

    def _add_to_parse_queue(self, payload):
        try:
            self.queue.publish(PARSE_QNAME, payload)
        except Exception as e:
            self._logger.error(f"Issue adding to the parser queue: {e}")

    def _consume_rabbit_message(self, ch, method, properties, body):
        try:
            # Process the message
            self._logger.info(f"Processing: {body.decode()}")
            url, depth = json.loads(body.decode())

            self._logger.info("Calling page crawl")
            self._crawl_pages(url, depth)

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            # Optionally reject the message (without requeue)
            # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    """" === Crawling Methods === """

    def _crawl_pages(self, url, depth):

        if not self.robot.allows_crawling(url):
            self._logger.warning(
                f"Skipping page: {url} - Robot.txt does not allow crawling it")
            self.db.save_skipped_page(url, None)
            return

        response = self.get_page(url)

        if response is None or response.status_code != 200:
            self._logger.error(
                f"Failed to get page: {url},  Status Code: {response.status_code}")
            self.db.save_failed_page_crawl(url, response.status_code)
            return

        links = self.extract_links(response.text, url)

        # if links is None:
        #     self._logger.warning(f"No links extracted from: {url}")
        #     self.skipped += 1
        #     return

        url_hash, filepath = self.downloader.download_compressed_html_content(
            os.getenv('DL_HTML_PATH'), url, response.text)

        page_id = self.db.save_crawled_page(
            (url, url_hash, filepath, response.status_code))

        new_depth = depth + 1

        if new_depth <= MAX_DEPTH:
            self.add_links_to_queue(page_id, links, new_depth)
        else:
            self._logger.info(
                f"Skipping links for url: {url} - links exceed the max depth of {MAX_DEPTH}")

        # Add url to visited set
        self.cache.add_to_visited_set(url)
        self._logger.info(f"Crawled URL: {url}")

    def get_page(self, url):
        try:
            response = self.fetcher.get(url, headers=BASE_HEADERS, timeout=10)
            return response
        except Exception as e:
            self._logger.error(f"Request failed for {url}: {e}")
            return None

    def extract_links(self, html_text, url):
        try:
            soup = BeautifulSoup(html_text, "lxml")
            return soup.select('#mw-content-text a')
        except Exception as e:
            self._logger.error(f"Parsing or DB error at {url}: {e}")
            return None

    def add_links_to_queue(self, page_id, links, new_depth):
        try:
            for link in links:
                to_url = link.get('href')

                if not to_url:
                    continue

                normalized_url = utils.normalize_url(to_url)

                if self.is_excluded(to_url):
                    continue

                if self.cache.is_queueable(normalized_url):
                    self._add_to_crawl_queue((normalized_url, new_depth))
                    self.cache.add_to_enqueued_set(normalized_url)
                    is_internal = not utils.is_external_link(normalized_url)
                    self.db.save_link(page_id, normalized_url, is_internal)
        except Exception as e:
            self._logger.error(f"Enqueue error adding link : {e}")

    def is_excluded(self, to_url):
        # ignore external urls and link tags with no href
        if (
            utils.is_home_page(to_url) or
            utils.is_external_link(to_url) or
            utils.has_excluded_prefix(to_url)
        ):
            return True
        return False

    """" === Temp Dev Logging Methods === """

    # TODO: pull this into the python-utility package
    # def clear_terminal(self):
    #     if platform.system() == "Windows":
    #         os.system("cls")
    #     else:
    #         os.system("clear")


if __name__ == "__main__":
    crawler = WebCrawler()
    crawler.queue.channel.start_consuming()

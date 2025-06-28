
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from crawler.robot_hander import RobotHandler
from crawler.download_handler import DownloadHandler
from crawler.fetcher import Fetcher
from dotenv import load_dotenv
from shared import utils
from shared.cache_service import CacheService
from shared.queue_service import QueueService
from shared.logger import setup_logging
from shared.config import BASE_HEADERS, CRAWLER_QUEUE_CHANNELS


class WebCrawler:
    def __init__(self):
        load_dotenv()
        self._logger = setup_logging(
            os.getenv('CRAWL_LOGS', 'logs/crawler.log')
        )

        # rabbitMQ setup
        self.queue = QueueService(
            self._logger,
            list(CRAWLER_QUEUE_CHANNELS.values())
        )
        self.queue.channel.basic_consume(
            queue=CRAWLER_QUEUE_CHANNELS['listen'],
            on_message_callback=self._consume_queue_message,
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

        # TODO: refactored db calls into messages to parser
        # self.db = DatabaseService(self._logger)

        self._logger.info('Crawler Initiation Complete')

    """" === RabiitMQ Methods === """

    # def _add_to_crawl_queue(self, payload):
    #     try:
    #         self.queue.publish(CRAWLER_QUEUE_CHANNELS['savepage'], payload)
    #     except Exception as e:
    #         self._logger.error(f"Issue adding to the crawler queue: {e}")

    # def _add_to_parse_queue(self, payload):
    #     try:
    #         self.queue.publish(CRAWLER_QUEUE_CHANNELS['parsejobs'], payload)
    #     except Exception as e:
    #         self._logger.error(f"Issue adding to the parser queue: {e}")

    def _publish_save_page_msg(self, page_data):
        try:
            url, url_hash, status_code, filepath, crawl_time = page_data
            payload = {
                "page_url": url,
                "url_hash": url_hash,
                "status_code": status_code,
                "compressed_path": filepath,
                "crawl_time": crawl_time
            }
            self.queue.publish(CRAWLER_QUEUE_CHANNELS['savepage'], payload)
            self._logger.debug(f"Published to save page '{url}'")
        except Exception as e:
            self._logger.error(
                f"Error publishing to {CRAWLER_QUEUE_CHANNELS['savepage']} - {e}"
            )

    def _publish_parse_content_msg(self, page_url, compressed_path):
        try:
            payload = {
                "page_url": page_url,
                "compressed_path": compressed_path,
            }
            self.queue.publish(CRAWLER_QUEUE_CHANNELS['parsejobs'], payload)
            self._logger.debug(f"Published to parse page")
        except Exception as e:
            self._logger.error(
                f"Error publishing to {CRAWLER_QUEUE_CHANNELS['parsejobs']} - {e}"
            )

    def _consume_queue_message(self, ch, method, properties, body):
        try:
            # Process the message
            self._logger.info(f"Processing: {body.decode()}")
            message = json.loads(body.decode())

            self._logger.info("Calling page crawl")
            self._crawl_pages(message['url'], message['depth'])

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")

    """" === Crawling Methods === """

    def _crawl_pages(self, url, depth):

        if not self.robot.allows_crawling(url):
            self._logger.warning(
                f"Skipping page: {url} - Robot.txt does not allow crawling it")
            # self.db.save_skipped_page(url, None)
            return

        response = self.get_page(url)
        status_code = response.status_code

        if response is None or status_code != 200:
            self._logger.error(
                f"Failed to get page: {url},  Status Code: {status_code}")
            # self.db.save_failed_page_crawl(url, status_code)
            return

        # links = self.extract_links(response.text, url)

        url_hash, filepath = self.downloader.download_compressed_html_content(
            os.getenv('DL_HTML_PATH'), url, response.text)

        crawl_time = datetime.now(ZoneInfo("America/New_York")).isoformat()

        self._publish_save_page_msg(
            (url, url_hash, status_code, filepath, crawl_time)
        )

        self._publish_parse_content_msg(url, filepath)

        # page_id =  self.db.save_crawled_page(
        #     (url, url_hash, filepath, status_code))

        # self._add_to_parse_queue((page_id, filepath))

        # new_depth = depth + 1

        # if new_depth <= MAX_DEPTH:
        #     self.add_links_to_queue(page_id, links, new_depth)
        # else:
        #     self._logger.info(
        #         f"Skipping links for url: {url} - links exceed the max depth of {MAX_DEPTH}")

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

    # def extract_links(self, html_text, url):
    #     try:
    #         soup = BeautifulSoup(html_text, "lxml")
    #         return soup.select('#mw-content-text a')
    #     except Exception as e:
    #         self._logger.error(f"Parsing or DB error at {url}: {e}")
    #         return None

    def add_links_to_queue(self, page_id, links, new_depth):
        try:
            for link in links:
                to_url = link.get('href')

                if not to_url:
                    continue

                normalized_url = utils.normalize_url(to_url)

                if self.is_excluded(to_url):
                    continue

                # TODO: clean up
                # if self.cache.is_queueable(normalized_url):
                    # self._add_to_crawl_queue((normalized_url, new_depth))
                    # self.cache.add_to_enqueued_set(normalized_url)
                    # is_internal= not utils.is_external_link(normalized_url)
                    # self.db.save_link(page_id, normalized_url, is_internal)
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

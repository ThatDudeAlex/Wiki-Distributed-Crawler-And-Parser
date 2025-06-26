
import os
import platform
import time
import pika
import redis
import requests
import json
import gzip
import hashlib
import urllib.robotparser
from utilities import utils
from shared.queue_service import QueueService
from shared.logger import setup_logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pika.exceptions import AMQPConnectionError
from ratelimit import limits, sleep_and_retry
from database.engine import SessionLocal
from database.db_models.models import Page, Link, CrawlStatus
from config import (SEED_URL, ROBOTS_TXT, BASE_HEADERS, MAX_DEPTH,
                    R_VISITED, R_ENQUEUED, CRAWL_QNAME, PARSE_QNAME)


class WebCrawler:
    def __init__(self):
        load_dotenv()
        self.logger = setup_logging(
            os.getenv('CRAWL_LOGS', 'logs/crawler.log')
        )
        # rabbitMQ setup
        self.crawl_queue_name = CRAWL_QNAME
        self.parse_queue_name = PARSE_QNAME

        self.queue = QueueService(
            self.crawl_queue_name, self.parse_queue_name, self.logger)

        self.queue.channel.basic_consume(
            queue=self.crawl_queue_name,
            on_message_callback=self._consume_rabbit_message,
            auto_ack=False
        )

        # redis setup
        self.redis = redis.Redis(
            host='redis', port=6379, decode_responses=True)

        # robot.txt setup
        self.rp = urllib.robotparser.RobotFileParser()
        self._setup_robot_text()

        # database setup
        self.db = SessionLocal()

        # TODO: move into the database
        # self.count = 0  # number of urls navigated to
        self.skipped = 0  # number of urls skipped

        # Only becomes true if it doesnt exist - This helps prevent the race condition of
        # multiple instances & allows only 1 instance to make the seed the queue
        queue_is_seeded = self.redis.set(f"enqueued:{SEED_URL}", 1, nx=True)

        if queue_is_seeded:
            self.redis.sadd(R_ENQUEUED, SEED_URL)
            self._add_to_crawl_queue((SEED_URL, 0))

        self.logger.info('Crawler Initiation Complete')

    """" === RabiitMQ Methods === """

    # def _setup_rabbit_connection(self):
    # self.connection = self._get_rabbit_connection()
    # creds = pika.PlainCredentials(
    #     os.environ["RABBITMQ_USER"],
    #     os.environ["RABBITMQ_PASSWORD"],
    # )
    # # connection = self._get_rabbit_connection()
    # self.connection = pika.BlockingConnection(
    #     pika.ConnectionParameters("rabbitmq", port=5672, credentials=creds))
    # self.channel = self.connection.channel()
    # self.channel.basic_qos(prefetch_count=1)
    # self.channel.queue_declare(queue=self.crawl_queue_name, durable=True)
    # self.channel.queue_declare(queue=self.parse_queue_name, durable=True)
    # self.channel.basic_consume(
    #     queue=self.crawl_queue_name,
    #     on_message_callback=self._consume_rabbit_message,
    #     auto_ack=False
    # )
    # queue = QueueService(self.crawl_queue_name,
    #                      self.parse_queue_name, self.logger)
    # queue.channel.basic_consume(
    #     queue=self.crawl_queue_name,
    #     on_message_callback=self._consume_rabbit_message,
    #     auto_ack=False
    # )
    # return queue

    def _add_to_crawl_queue(self, payload):
        try:
            self.queue.publish(self.crawl_queue_name, payload)
        except Exception as e:
            self.logger.error(f"Issue adding to the crawler queue: {e}")

    def _add_to_parse_queue(self, payload):
        try:
            self.queue.publish(self.parse_queue_name, payload)
        except Exception as e:
            self.logger.error(f"Issue adding to the parser queue: {e}")

    def _consume_rabbit_message(self, ch, method, properties, body):
        try:
            # Process the message
            self.logger.info(f"Processing: {body.decode()}")
            url, depth = json.loads(body.decode())

            self.logger.info("Calling page crawl")
            self._crawl_pages(url, depth)

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self.logger.error(f"Failed to process message: {str(e)}")
            # Optionally reject the message (without requeue)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    """" === Robot.txt Methods === """

    def _setup_robot_text(self):
        self.rp.set_url(ROBOTS_TXT)
        self.rp.read()

    def robot_allows_crawling(self, url):
        if not self.rp.can_fetch(BASE_HEADERS['user-agent'], url):
            self.logger.warning(f"Blocked by robots.txt: {url}")
            return False
        return True

    """" === Crawling Methods === """

    # TODO: Implement adding data to the DB
    def _crawl_pages(self, url, depth):
        # self._current_status_report(depth)

        if not self.robot_allows_crawling(url) or depth > MAX_DEPTH:
            self.logger.warning(f"Robot prevents crawling into: {url}")
            self.skipped += 1
            return

        response = self.get_page(url)

        if response is None or response.status_code != 200:
            self.logger.warning(
                f"Failed to get page: {url},  Status Code: {response.status_code}")
            self.skipped += 1
            return

        links = self.extract_links(response.text, url)

        if links is None:
            self.logger.warning(f"No links extracted from: {url}")
            self.skipped += 1
            return

        url_hash, filepath = self.download_compressed_html(url, response.text)

        page_id = self.save_page(
            (url, url_hash, filepath, CrawlStatus.CRAWLED_SUCCESS, response.status_code))

        new_depth = depth + 1

        if new_depth <= MAX_DEPTH:
            self.add_links_to_queue(page_id, links, new_depth)
        else:
            self.logger.info(
                f"Skipping links for url: {url} - links exceed the max depth of {MAX_DEPTH}")

        # Add url to visited set
        self.redis.sadd(R_VISITED, url)
        self.logger.info(f"Crawled URL: {url}")

    @sleep_and_retry
    @limits(calls=1, period=1)  # 1 request per second
    def get_page(self, url):
        try:
            response = requests.get(url, headers=BASE_HEADERS, timeout=10)
            if response.status_code != 200:
                self.logger.warning(
                    f"Non-200 response ({response.status_code}) for {url}"
                )
            return response
        except Exception as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return None

    def extract_links(self, html_text, url):
        try:
            soup = BeautifulSoup(html_text, "lxml")
            return soup.select('#mw-content-text a')
        except Exception as e:
            self.logger.error(f"Parsing or DB error at {url}: {e}")
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

                # TODO: Add url into queue and enqueued set
                if self.is_queueable(normalized_url):
                    self._add_to_crawl_queue((normalized_url, new_depth))
                    self.redis.sadd(R_ENQUEUED, normalized_url)
                    # TODO: cleanup after successful implementation
                    # queue.add((normalized_to_url, depth + 1))
                    # enqueued_set.add(normalized_to_url)

                    # TODO: add normalized URL to the DB
                    is_internal = not utils.is_external_link(normalized_url)
                    self.save_link(page_id, normalized_url, is_internal)
                    # DB.add_link(page_id, normalized_to_url)
        except Exception as e:
            self.logger.error(f"Enqueue error adding link : {str(e)}")

    def is_excluded(self, to_url):
        # ignore external urls and link tags with no href
        if (
            utils.is_home_page(to_url) or
            utils.is_external_link(to_url) or
            utils.has_excluded_prefix(to_url)
        ):
            return True
        return False

    # TODO: Once redis is implemented updated if statement to use redis for the sets
    def is_queueable(self, normalized_url):
        in_visited = self.redis.sismember(R_VISITED, normalized_url)
        in_enqueued = self.redis.sismember(R_ENQUEUED, normalized_url)

        if in_visited or in_enqueued:
            return False
        return True

    def download_compressed_html(self, url, html_content):
        url_hash = self._hash_url(url)
        filename = f"{url_hash}.html.gz"
        filepath = os.path.join(os.getenv('DL_HTML_PATH'), filename)

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(
            f"Downloaded compressed HTML for URL: {url} - filepath: {filepath}")
        return (url_hash, filepath)

    """" === DB Methods === """

    def save_page(self, crawl_data):
        url, url_hash, filepath, crawl_status, status_code = crawl_data
        page = Page(
            url=url,
            url_hash=url_hash,
            last_crawl_status=crawl_status,
            http_status_code=status_code,
            compressed_path=filepath)
        self.db.add(page)
        self.db.commit()
        return page.id

    def save_link(self, page_id, target_url, is_internal=False):
        link = Link(
            source_page_id=page_id,
            target_url=target_url,
            is_internal=is_internal
        )
        self.db.add(link)
        self.db.commit()

    def _hash_url(self, url):
        # Create a SHA-256 hash object
        hash_object = hashlib.sha256()

        # Update the hash object with the bytes of the url string
        hash_object.update(url.encode())

        # return the hexadecimal representation of the hash
        return hash_object.hexdigest()

    """" === Temp Dev Logging Methods === """

    # TODO: pull this into the python-utility package
    def clear_terminal(self):
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    # def _current_status_report(self, depth):
    #     self.clear_terminal()
    #     # self.logger.info(f"Pages Crawled :  {self.count}")
    #     self.logger.info(f"Pages Skipped :  {self.skipped}")
    #     self.logger.info(f"Current Depth :  {depth}\n")


if __name__ == "__main__":
    crawler = WebCrawler()
    crawler.queue.channel.start_consuming()

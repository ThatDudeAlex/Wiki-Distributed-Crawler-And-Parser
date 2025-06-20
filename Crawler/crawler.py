
import os
import platform
import time
import requests
import logging
import urllib.robotparser
from utilities import utils
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry
from .init_logging import setup_logging
from config import SEED_URL, ROBOTS_TXT, BASE_HEADERS, MAX_DEPTH


class WebCrawler:
    def __init__(self, logger: logging.Logger):
        self.is_running = False
        self.logger = logger
        self.count = 0  # number of urls navigated to
        self.skipped = 0  # number of urls skipped
        self.rp = urllib.robotparser.RobotFileParser()

    def robot_allows_crawling(self, url):
        if not self.rp.can_fetch(BASE_HEADERS['user-agent'], url):
            self.logger.warning(f"Blocked by robots.txt: {url}")
            return False
        return True

    # TODO: Implement adding data to the DB

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
            self.logger.error(f"Request failed for {url}: {e}")
            return None

    def extract_links(self, html_text, url):
        try:
            soup = BeautifulSoup(html_text, "lxml")
            return soup.select('#mw-content-text a')
        except Exception as e:
            self.logger.error(f"Parsing or DB error at {url}: {e}")
            return None

    def add_links_to_queue(self, page_id, links, depth):
        try:
            for link in links:
                to_url = link.get('href')

                if self.is_excluded(to_url):
                    continue

                normalized_to_url = utils.normalize_url(to_url)

                # TODO: Add url into queue and enqueued set
                if self.is_queueable(normalized_to_url):
                    continue
                    # queue.add((normalized_to_url, depth + 1))
                    # enqueued_set.add(normalized_to_url)

                    # TODO: add normalized URL to the DB
                    # DB.add_link(page_id, normalized_to_url)
        except Exception as e:
            self.logger.error(f"Enqueue error adding link : {e}")

    def is_excluded(self, to_url):
        # ignore external urls and link tags with no href
        if (
            to_url is None or
            utils.is_external_link(to_url) or
            utils.has_excluded_prefix(to_url)
        ):
            return True
        return False

    # TODO: Once redis is implemented updated if statement to use redis for the sets
    def is_queueable(self, normalized_to_url):
        # if normalized_to_url in self.visited_set or normalized_to_url in self.enqueued_set:
        #     return False
        return True

    def clear_terminal(self):
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    def _current_status_report(self, depth):
        self.clear_terminal()
        print(f"Pages Crawled :  {self.count}")
        print(f"Pages Skipped :  {self.skipped}")
        print(f"Current Depth :  {depth}\n")

    def _crawl_pages(self):
        # TODO: Implement receiving messages from rabbitMQ
        url, depth = queue.message
        self._current_status_report(depth)

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

        # Add Page into db: page_id = add(url, url_hash)

        # Add links to queue
        # self.add_links_to_queue(page_id, links, depth)

        # Add page to visited set: visited_set.add(url)
        self.count += 1

    def stop(self):
        self.logger.info('Stopping The Crawler\n')
        self.is_running = False
        # TODO: remove method if nothing else is added or using this

    def run(self):
        self.logger.info('Crawler Initiated & Running')
        self.rp.set_url(ROBOTS_TXT)
        self.rp.read()
        self.is_running = True

        # TODO: Implement adding to the crawl queue and enqueued set with redis
        # queue.add((SEED_URL, 0))
        # enqueued_set.add(SEED_URL)

        self._crawl_pages()
        self.logger.info('\n✅ Crawler Finished Succesfully!\n')
        self.stop()


if __name__ == "__main__":
    load_dotenv()
    logger = setup_logging(os.getenv('CRAWL_LOGS', '../logs/crawler.log'))

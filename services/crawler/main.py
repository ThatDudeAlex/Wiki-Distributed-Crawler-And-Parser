# TODO: Use Pydantic BaseSettings to configure settings in main.py
# TODO: Use my logger package to setup the logger
import os
from shared.config import CRAWLER_QUEUE_CHANNELS, MAX_DEPTH
from shared.queue_service import QueueService
from service.crawler_service import CrawlerService
from message_handler import start_crawl_listener
from shared.logger import setup_logging


def main():
    logger = setup_logging(
        os.getenv('CRAWL_LOGS', 'logs/crawler.log')
    )

    queue_service = QueueService(logger, list(CRAWLER_QUEUE_CHANNELS.values()))

    crawler_service = CrawlerService(queue_service, logger, MAX_DEPTH)

    # This starts consuming messages and routes them to the crawler_service
    start_crawl_listener(queue_service, crawler_service, logger)


if __name__ == "__main__":
    main()

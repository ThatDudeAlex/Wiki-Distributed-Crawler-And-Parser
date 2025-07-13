
from prometheus_client import start_http_server
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.queue_service import QueueService
from components.crawler.configs.crawler_config import configs
from components.crawler.services.crawler_service import CrawlerService
from components.crawler.message_handler import start_crawl_listener
from shared.logging_utils import get_logger


def main():
    logger = get_logger(
        configs.logging.logger_name, configs.logging.log_level
    )
    start_http_server(8000)
    logger.info("Prometheus metrics exposed on port 8000")

    queue_service = QueueService(logger, CrawlerQueueChannels.get_values())

    crawler_service = CrawlerService(configs, queue_service, logger)

    # This starts consuming messages and routes them to the crawler_service
    start_crawl_listener(queue_service, crawler_service, logger)


if __name__ == "__main__":
    main()

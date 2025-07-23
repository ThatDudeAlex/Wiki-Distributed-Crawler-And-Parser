"""
Main entrypoint for the Crawler Component:s
    - Loads configuration and initializes logging
    - Sets up Prometheus metrics endpoint
    - Starts message consumption loop
"""

from prometheus_client import start_http_server
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels
from shared.rabbitmq.queue_service import QueueService
from components.crawler.services.crawler_service import CrawlerService
from components.crawler.services.message_handler import start_crawler_listener
from shared.logging_utils import get_logger
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "crawler"

def run():
    configs = component_config_loader(COMPONENT_NAME)
    logger = get_logger(
        configs['logging']['logger_name'], configs['logging']['log_level']
    )

    logger.info(f"Starting {COMPONENT_NAME} component")

    queue_service = QueueService(logger, CrawlerQueueChannels.get_values())

    # TODO: Add prometheus configs into yml files
    prometheus_port = configs.get("monitoring", {}).get("port", 8000)
    start_http_server(prometheus_port)
    logger.info(f"Prometheus metrics exposed on port {prometheus_port}")

    crawler_service = CrawlerService(configs, queue_service, logger)

    # This starts consuming messages and routes them to the crawler_service
    start_crawler_listener(queue_service, crawler_service, logger)


if __name__ == "__main__":
    run()

import signal
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

    queue_service = QueueService(logger, CrawlerQueueChannels.get_values())

    # TODO: remove if not needed or useful
    def graceful_shutdown(signum, frame):
        logger.info("Received termination signal. Shutting down cleanly...")
        queue_service.close()

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    start_http_server(8000)
    logger.info("Prometheus metrics exposed on port 8000")

    crawler_service = CrawlerService(configs, queue_service, logger)

    # This starts consuming messages and routes them to the crawler_service
    start_crawler_listener(queue_service, crawler_service, logger)


if __name__ == "__main__":
    run()

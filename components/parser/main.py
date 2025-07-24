from prometheus_client import start_http_server
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.queue_service import QueueService
from components.parser.services.parsing_service import ParsingService
from components.parser.message_handler import start_parser_listener
from shared.logging_utils import get_logger
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "parser"

def run():
    configs = component_config_loader(COMPONENT_NAME, True)
    logger = get_logger(
        configs['logging']['logger_name'], configs['logging']['log_level']
    )

    start_http_server(8000)
    logger.info("Prometheus metrics exposed on port 8000")

    queue_service = QueueService(logger, ParserQueueChannels.get_values())

    parsing_service = ParsingService(configs, queue_service, logger)

    # This starts consuming messages and routes them to the parsing_service
    start_parser_listener(queue_service, parsing_service, logger)


if __name__ == "__main__":
    run()

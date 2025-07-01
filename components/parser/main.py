from components.parser.configs.app_configs import PARSER_QUEUE_CHANNELS
from rabbitmq.queue_service import QueueService
from components.parser.services.parsing_service import ParsingService
from components.parser.message_handler import start_parser_listener
from shared.logging_utils import get_logger


def main():
    logger = get_logger('Parser')

    queue_service = QueueService(logger, list(PARSER_QUEUE_CHANNELS.values()))

    parsing_service = ParsingService(queue_service, logger)

    # This starts consuming messages and routes them to the parsing_service
    start_parser_listener(queue_service, parsing_service, logger)


if __name__ == "__main__":
    main()

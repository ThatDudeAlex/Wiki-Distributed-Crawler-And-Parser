from components.db_writer.services.message_handler import start_db_service_listener
from shared.logging_utils import get_logger
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels
from shared.rabbitmq.queue_service import QueueService


def main():
    """
    Entrypoint for the db_writer service
    """
    logger = get_logger("db_writer")
    try:
        queue_service = QueueService(logger, DbWriterQueueChannels.get_values())
        start_db_service_listener(queue_service, logger)
    except Exception:
        logger.exception("Unhandled exception in db_writer service")


if __name__ == "__main__":
    main()

from shared.logging_utils import get_logger
from rabbitmq.queue_service import QueueService
from shared.config import DB_SERVICE_QUEUE_CHANNELS
from components.db_writer.message_handler import start_db_writer_listener


def run():
    logger = get_logger("DB_Writer")
    queue_service = QueueService(
        logger,
        list(DB_SERVICE_QUEUE_CHANNELS.values())
    )

    start_db_writer_listener(queue_service, logger)


if __name__ == "__main__":
    run()

from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels
from components.db_writer.message_handler import start_db_service_listener


def run():
    logger = get_logger("db_writer")
    queue_service = QueueService(logger, DbWriterQueueChannels.get_values())

    start_db_service_listener(queue_service, logger)


if __name__ == "__main__":
    run()

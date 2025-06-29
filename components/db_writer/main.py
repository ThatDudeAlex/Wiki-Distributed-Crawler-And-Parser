from shared.logging_utils import get_logger
from shared.queue_service import QueueService
from shared.config import DB_SERVICE_QUEUE_CHANNELS


def run():
    logger = get_logger("DB_Writer")
    queue_service = QueueService(
        logger,
        list(DB_SERVICE_QUEUE_CHANNELS.values())
    )

    queue_service.channel.basic_consume(..., ...)
    queue_service.channel.start_consuming()


if __name__ == "__main__":
    run()

from shared.config import SEED_URL, ALL_QUEUE_CHANNELS, QueueNames
from shared.logging_utils import get_logger
from rabbitmq.queue_service import QueueService


if __name__ == "__main__":
    logger = get_logger('RabbitMQ_Seeder')

    queue = QueueService(logger, ALL_QUEUE_CHANNELS)

    queue.publish(QueueNames.CRAWL.value, {
        "url": SEED_URL,
        "depth": 0,
    })
    logger.info("Seeded Queue with URL: %s", SEED_URL)

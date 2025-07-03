from shared.logging_utils import get_logger
from shared.rabbitmq.enums.queue_names import QueueNames
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.queue_config import ALL_QUEUE_CHANNELS
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.utils import get_timestamp_eastern_time
from shared.config import SEED_URL

if __name__ == "__main__":
    logger = get_logger('RabbitMQ_Seeder')

    queue = QueueService(logger, ALL_QUEUE_CHANNELS)

    message = CrawlTask(
        url=SEED_URL,
        depth=0,
        scheduled_at=get_timestamp_eastern_time()
    )
    message.validate_publish()

    queue.publish(QueueNames.CRAWL_TASK.value, message)
    logger.info("Seeded Queue with URL: %s", SEED_URL)

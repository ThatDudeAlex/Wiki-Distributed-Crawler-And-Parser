from shared.logging_utils import get_logger
from shared.rabbitmq.enums.queue_names import QueueNames
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.queue_config import ALL_QUEUE_CHANNELS
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.schemas.link_processing_schemas import AddLinksToSchedule
from shared.utils import get_timestamp_eastern_time
from shared.config import SEED_URL

if __name__ == "__main__":
    logger = get_logger('RabbitMQ_Seeder')

    source_page_url: str
    url: str
    depth: int
    discovered_at: str
    queue = QueueService(logger, ALL_QUEUE_CHANNELS)

    links = [CrawlTask(
        url=SEED_URL,
        depth=0,
        scheduled_at=get_timestamp_eastern_time()
    )]
    message = AddLinksToSchedule(links=links)
    message.validate_publish()

    # queue.publish(QueueNames.URLS_TO_CRAWL.value, message)
    queue.publish(QueueNames.ADD_LINKS_TO_SCHEDULE.value, message)
    logger.info("Seeded Queue with URL: %s", SEED_URL)

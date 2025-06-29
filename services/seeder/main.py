import os
from shared.config import SEED_URL, ALL_QUEUE_CHANNELS, QueueNames
from shared.logging_utils import get_logger
from shared.queue_service import QueueService

logger = get_logger('Seeder')

queue = QueueService(logger, ALL_QUEUE_CHANNELS)

queue.publish(QueueNames.CRAWL.value, {
    "url": SEED_URL,
    "depth": 0,
})

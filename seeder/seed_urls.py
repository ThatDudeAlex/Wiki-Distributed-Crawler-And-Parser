import os
from datetime import datetime
from shared.config import SEED_URL, ALL_QUEUE_CHANNELS, QueueNames
from shared.logger import setup_logging
from shared.queue_service import QueueService

logger = setup_logging(
    os.getenv('SEEDER_LOGS', 'logs/url_seeder.log')
)

queue = QueueService(logger, ALL_QUEUE_CHANNELS)

queue.publish(QueueNames.CRAWL.value, {
    "url": SEED_URL,
    "depth": 0,
})

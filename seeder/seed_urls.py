import os
from datetime import datetime
from shared.config import SEED_URL
from shared.logger import setup_logging
from shared.queue_service import QueueService

logger = setup_logging(
    os.getenv('SEEDER_LOGS', 'logs/url_seeder.log')
)

queue = QueueService(logger)

queue.publish("crawl_tasks", {
    "url": SEED_URL,
    "depth": 0,
    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
})

from shared.logging_utils import get_logger
from rabbitmq.queue_service import QueueService
from components.scheduler.configs.app_configs import SCHEDULER_QUEUE_CHANNELS
from components.scheduler.message_handler import start_schedule_listener


def run():
    logger = get_logger("Scheduler")
    queue_service = QueueService(
        logger,
        SCHEDULER_QUEUE_CHANNELS.values()
    )

    start_schedule_listener(queue_service, logger)


if __name__ == "__main__":
    run()

from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels, SchedulerLeakyBucket
from components.scheduler.message_handler import start_schedule_listener
from components.scheduler.services.schedule_service import ScheduleService


def run():
    logger = get_logger("Scheduler")

    queue_service = QueueService(logger, SchedulerQueueChannels.get_values())
    queue_service.setup_delay_queue(
        delay_queue_name=SchedulerLeakyBucket.LEAKY_BUCKET.value,
        processing_queue_name=SchedulerQueueChannels.SCHEDULED_LINKS_TO_PROCESS.value,
    )

    scheduler_service = ScheduleService(queue_service, logger)

    start_schedule_listener(scheduler_service, queue_service, logger)


if __name__ == "__main__":
    run()

"""
Main entry point for the Scheduler component

Initializes configuration, logging, queue service, and starts the schedule listener
to handle incoming scheduling tasks via RabbitMQ
"""

import logging
from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from components.scheduler.services.message_handler import start_schedule_listener
from components.scheduler.services.schedule_service import ScheduleService
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "scheduler"

def run(configs_override=None):
    configs = configs_override or component_config_loader(COMPONENT_NAME, True)
    logger = get_logger(
        configs['logging']['logger_name'], configs['logging']['log_level']
    )

    logger.info("🚀 Scheduler service is starting up...")

    queue_service = QueueService(logger, SchedulerQueueChannels.get_values())
    scheduler_service = ScheduleService(configs, queue_service, logger)
    start_schedule_listener(scheduler_service, queue_service, logger)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(COMPONENT_NAME).exception("Fatal error during scheduler startup")

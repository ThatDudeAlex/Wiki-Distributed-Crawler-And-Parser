from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from components.rescheduler.services.rescheduler_service import Rescheduler
from shared.rabbitmq.enums.queue_names import ReschedulerQueueChannels
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "rescheduler"

def main():
    configs = component_config_loader(COMPONENT_NAME)
    logger = get_logger(
        configs['logging']['logger_name'], configs['logging']['log_level']
    )

    queue_service = QueueService(logger, ReschedulerQueueChannels.get_values())

    dispatcher = Rescheduler(configs, queue_service, logger)

    logger.info("Starting Rescheduler Component...")
    dispatcher.run()


if __name__ == "__main__":
    main()

from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from components.rescheduler.configs.rescheduler_config import configs
from shared.rabbitmq.enums.queue_names import ReschedulerQueueChannels

from components.rescheduler.services.rescheduler_service import Rescheduler


# TODO: FINISH implementation
def run():
    logger = get_logger(
        configs.logging.logger_name, configs.logging.log_level
    )

    queue_service = QueueService(logger, ReschedulerQueueChannels.get_values())

    dispatcher = Rescheduler(configs, queue_service, logger)

    dispatcher.run()


if __name__ == "__main__":
    run()

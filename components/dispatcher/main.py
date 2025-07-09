from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from components.dispatcher.configs.dispatcher_config import configs
from shared.rabbitmq.enums.queue_names import DispatcherQueueChannels
from components.dispatcher.services.dispatching_service import Dispatcher


def run():
    logger = get_logger(
        configs.logging.logger_name, configs.logging.log_level
    )

    queue_service = QueueService(logger, DispatcherQueueChannels.get_values())

    dispatcher = Dispatcher(configs, queue_service, logger)

    dispatcher.run()


if __name__ == "__main__":
    run()

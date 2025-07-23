from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DispatcherQueueChannels
from components.dispatcher.services.dispatching_service import Dispatcher
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "dispatcher"

def run():
    configs = component_config_loader(COMPONENT_NAME)
    logger = get_logger(
        configs['logging']['logger_name'], configs['logging']['log_level']
    )

    queue_service = QueueService(logger, DispatcherQueueChannels.get_values())

    dispatcher = Dispatcher(configs, queue_service, logger)

    dispatcher.run()


if __name__ == "__main__":
    run()

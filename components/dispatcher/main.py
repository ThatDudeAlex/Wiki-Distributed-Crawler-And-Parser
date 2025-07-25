from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DispatcherQueueChannels
from components.dispatcher.services.dispatching_service import Dispatcher
from shared.configs.config_loader import component_config_loader

COMPONENT_NAME = "dispatcher"

def run() -> None:
    """
    Dispatcher Component Entrypoint

    Responsible for:
        - Loading configurations
        - Initializing logger and RabbitMQ queue service
        - Running the Dispatcher service
    """
    dispatcher_configs = component_config_loader(COMPONENT_NAME)

    # TODO: look into whether using a pydantic class using dict.get() with a default would
    #       be a better way to access the configuration values
    logger = get_logger(
        dispatcher_configs['logging']['logger_name'],
        dispatcher_configs['logging']['log_level']
    )

    queue_service = QueueService(logger, DispatcherQueueChannels.get_values())

    dispatcher = Dispatcher(dispatcher_configs, queue_service, logger)

    logger.info("Starting Dispatcher Component...")
    dispatcher.run()


if __name__ == "__main__":
    run()

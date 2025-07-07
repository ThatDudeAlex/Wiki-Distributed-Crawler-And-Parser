from shared.logging_utils import get_logger
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DispatcherQueueChannels
from components.dispatcher.services.dispatching_service import Dispatcher


def run():
    logger = get_logger("Dispatcher")
    queue_service = QueueService(logger, DispatcherQueueChannels.get_values())
    dispatcher = Dispatcher(queue_service, logger)
    dispatcher.run()


if __name__ == "__main__":
    run()

from prometheus_client import start_http_server
from components.db_writer.services.message_handler import start_db_service_listener
from shared.logging_utils import get_logger
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels
from shared.rabbitmq.queue_service import QueueService


def main():
    """
    Entrypoint for the db_writer service
    """
    logger = get_logger("db_writer")
    try:
        queue_service = QueueService(logger, DbWriterQueueChannels.get_values())
        # TODO: add component configs during cleanup
        # If needed put port as part of a component config ()
        prometheus_port = 8000
        start_http_server(prometheus_port)
        logger.info(f"Prometheus metrics exposed on port {prometheus_port}")

        start_db_service_listener(queue_service, logger)
    except Exception:
        logger.exception("Unhandled exception in db_writer service")


if __name__ == "__main__":
    main()

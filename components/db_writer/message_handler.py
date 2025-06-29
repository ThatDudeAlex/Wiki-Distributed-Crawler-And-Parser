from functools import partial
import json
import logging
from components.db_writer.core.db_writer import save_crawled_page, save_parsed_page_content
from shared.queue_service import QueueService
from shared.config import DB_SERVICE_QUEUE_CHANNELS
# from components.db_writer.configs.types import SavePageTask

# TODO: implement pydantic types to perform validation on messages received


def handle_save_page_message(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        save_crawled_page(message, logger)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error(f"Message Skipped - Invalid task message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        # maybe requeue for OperationalError or add a dead-letter queue
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def handle_save_parsed_content_message(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        save_parsed_page_content(message, logger)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e.json())
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        # maybe requeue for OperationalError or add a dead-letter queue
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_db_writer_listener(queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_save_page_partial = partial(
        handle_save_page_message, logger=logger
    )
    handle_save_page_content_partial = partial(
        handle_save_parsed_content_message, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=DB_SERVICE_QUEUE_CHANNELS['savepage'],
        on_message_callback=handle_save_page_partial,
        auto_ack=False
    )
    queue_service.channel.basic_consume(
        queue=DB_SERVICE_QUEUE_CHANNELS['savecontent'],
        on_message_callback=handle_save_page_content_partial,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service.channel.start_consuming()

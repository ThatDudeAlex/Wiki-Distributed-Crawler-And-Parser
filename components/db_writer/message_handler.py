from functools import partial
import json
import logging
from components.db_writer.core.db_writer import save_crawl_data, save_parsed_data
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels

# TODO: implement pydantic types to perform validation on messages received


def consume_save_crawl_data(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        save_crawl_data(message, logger)

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


def consume_save_parsed_data(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        save_parsed_data(message, logger)

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


def start_db_writer_listener(queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    save_crawl_data_partial = partial(
        consume_save_crawl_data, logger=logger
    )
    save_parsed_data_partial = partial(
        consume_save_parsed_data, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=DbWriterQueueChannels.SAVE_CRAWL_DATA,
        on_message_callback=save_crawl_data_partial,
        auto_ack=False
    )
    queue_service.channel.basic_consume(
        queue=DbWriterQueueChannels.SAVE_PARSED_DATA,
        on_message_callback=save_parsed_data_partial,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service.channel.start_consuming()

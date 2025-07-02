from functools import partial
import json
import logging
from components.db_service.core.db_service import fetch_page_metadata
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels
from shared.rabbitmq.schemas.crawling_task_schemas import FetchPageMetadata

# TODO: implement pydantic types to perform validation on messages received


def consume_fetch_page_metadata(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.info("Received fetch page message")
        message = json.loads(body.decode())
        task = FetchPageMetadata.model_validate_json(message)

        fetch_page_metadata(str(task.url), logger)

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
    fetch_page_metadata_partial = partial(
        consume_fetch_page_metadata, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=DbWriterQueueChannels.FETCH_PAGE_DATA,
        on_message_callback=fetch_page_metadata_partial,
        auto_ack=False
    )
    # queue_service.channel.basic_consume(
    #     queue=DbWriterQueueChannels.SAVE_PARSED_DATA,
    #     on_message_callback=save_parsed_data_partial,
    #     auto_ack=False
    # )

    logger.info("Listening for Database requests...")
    queue_service.channel.start_consuming()

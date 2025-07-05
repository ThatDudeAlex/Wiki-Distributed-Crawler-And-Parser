from functools import partial
import json
import logging
from components.db_writer.core.db_writer import cache_seen_url, save_page_metadata, save_parsed_data, save_processed_links
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import DbServiceQueueChannels
from shared.rabbitmq.schemas.crawling_task_schemas import SavePageMetadataTask
from shared.rabbitmq.schemas.link_processing_schemas import CacheSeenUrls, SaveProcessedLinks
from shared.rabbitmq.schemas.parsing_task_schemas import ParsedContent


def consume_save_page_metadata(ch, method, properties, body, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = SavePageMetadataTask(**message_dict)
        task.validate_consume()

        logger.info("Initiating Save Page Metadata Task: %s", task.url)
        save_page_metadata(task, logger)

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


def consume_save_parsed_content(ch, method, properties, body, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = ParsedContent(**message_dict)
        task.validate_consume()

        save_parsed_data(task, logger)

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


def consume_save_processed_Links(ch, method, properties, body, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = SaveProcessedLinks(**message_dict)
        task.validate_consume()

        save_processed_links(task, logger)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        # maybe requeue for OperationalError or add a dead-letter queue
        logger.error("Error processing message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def consume_cache_seen_url(ch, method, properties, body, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = CacheSeenUrls(**message_dict)
        task.validate_consume()

        cache_seen_url(task, logger)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        # maybe requeue for OperationalError or add a dead-letter queue
        logger.error("Error processing message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_db_service_listener(queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function.
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    save_page_metadata_partial = partial(
        consume_save_page_metadata, logger=logger
    )
    save_parsed_content_partial = partial(
        consume_save_parsed_content, logger=logger
    )
    save_save_processed_Links_partial = partial(
        consume_save_processed_Links, logger=logger
    )
    save_cache_seen_url_partial = partial(
        consume_cache_seen_url, logger=logger
    )

    # Save Page Metadata
    queue_service.channel.basic_consume(
        queue=DbServiceQueueChannels.SAVE_CRAWL_DATA,
        on_message_callback=save_page_metadata_partial,
        auto_ack=False
    )
    # Save Parsed Content
    queue_service.channel.basic_consume(
        queue=DbServiceQueueChannels.SAVE_PARSED_DATA,
        on_message_callback=save_parsed_content_partial,
        auto_ack=False
    )
    # Save Processed Links
    queue_service.channel.basic_consume(
        queue=DbServiceQueueChannels.SAVE_PROCESSED_LINKS,
        on_message_callback=save_save_processed_Links_partial,
        auto_ack=False
    )
    # Cache Processed Links
    queue_service.channel.basic_consume(
        queue=DbServiceQueueChannels.CACHE_PROCESSED_LINKS,
        on_message_callback=save_cache_seen_url_partial,
        auto_ack=False
    )

    logger.info("Listening for Database requests...")
    queue_service.channel.start_consuming()

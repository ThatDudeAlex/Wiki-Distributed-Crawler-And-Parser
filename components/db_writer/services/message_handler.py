import logging
from functools import partial

from shared.rabbitmq.enums.queue_names import DbWriterQueueChannels
from shared.rabbitmq.queue_service import QueueService
from components.db_writer.core.db_writer import (
    add_links_to_schedule,
    save_page_metadata,
    save_parsed_data,
    save_processed_links)
from shared.rabbitmq.schemas.save_to_db import (
    SaveLinksToSchedule,
    SavePageMetadataTask,
    SaveParsedContent,
    SaveProcessedLinks)


def consume_save_page_metadata(ch, method, properties, body, logger: logging.Logger):
    """
    Consume and process a message to save the metadata of a crawled page to the database

    Parses the message into a SavePageMetadataTask, writes it to the database,
    and acknowledges or rejects the message based on success or failure.

    Args:
        ch: The RabbitMQ channel
        method: Delivery method information including delivery tag
        properties: Message properties (unused)
        body: Raw message payload (bytes)
        logger (logging.Logger): Logger instance
    """
    try:
        message_str = body.decode('utf-8')
        task = SavePageMetadataTask.model_validate_json(message_str)

        logger.info("Initiating Task - Save Page Metadata: %s", task)
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
    """
    Consume and process a message to save parsed page content and categories

    Parses the message into a SaveParsedContent object and writes it to the
    PageContent table. Acknowledges or rejects the message based on outcome.

    Args:
        ch: The RabbitMQ channel
        method: Delivery method information including delivery tag
        properties: Message properties (unused)
        body: Raw message payload (bytes)
        logger (logging.Logger): Logger instance
    """
    try:
        message_str = body.decode('utf-8')
        task = SaveParsedContent.model_validate_json(message_str)

        logger.info("Initiating Task - Save Parsed Data: %s", task)
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


def consume_save_processed_links(ch, method, properties, body, logger: logging.Logger):
    """
    Consume and process a message containing links extracted from a page

    Parses the message into a SaveProcessedLinks object and performs a bulk
    upsert into the Link table. Acknowledges or rejects the message accordingly.

    Args:
        ch: The RabbitMQ channel
        method: Delivery method information including delivery tag
        properties: Message properties (unused)
        body: Raw message payload (bytes)
        logger (logging.Logger): Logger instance
    """
    try:
        message_str = body.decode('utf-8')
        task = SaveProcessedLinks.model_validate_json(message_str)

        logger.info("Initiating Task - Save Processed Links: %s", task)
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


def consume_add_links_to_schedule(ch, method, properties, body, logger: logging.Logger):
    """
    Consume and process a message to schedule new links for crawling

    Parses the message into a SaveLinksToSchedule object and inserts new
    links into the ScheduledLinks table. Acknowledges or rejects the message.

    Args:
        ch: The RabbitMQ channel
        method: Delivery method information including delivery tag
        properties: Message properties (unused)
        body: Raw message payload (bytes)
        logger (logging.Logger): Logger instance
    """
    try:
        message_str = body.decode('utf-8')

        task = SaveLinksToSchedule.model_validate_json(message_str)
        logger.info('got a message: %s', task)
        
        logger.info("Initiating Task - Add Links To Schedule: %s", task)
        add_links_to_schedule(task, logger)

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
    """
    Starts listening to database-write related RabbitMQ queues and redirects each to its corresponding consumer

    Args:
        queue_service (QueueService): The shared queue abstraction for subscribing to messages
        logger (logging.Logger): Logger instance
    """
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
        consume_save_processed_links, logger=logger
    )
    add_links_to_schedule_partial = partial(
        consume_add_links_to_schedule, logger=logger
    )

    # Save Page Metadata
    queue_service._channel.basic_consume(
        queue=DbWriterQueueChannels.PAGE_METADATA_TO_SAVE,
        on_message_callback=save_page_metadata_partial,
        auto_ack=False
    )
    # Save Parsed Content
    queue_service._channel.basic_consume(
        queue=DbWriterQueueChannels.PARSED_CONTENT_TO_SAVE,
        on_message_callback=save_parsed_content_partial,
        auto_ack=False
    )
    # Save Processed Links
    queue_service._channel.basic_consume(
        queue=DbWriterQueueChannels.SCHEDULED_LINKS_TO_SAVE,
        on_message_callback=save_save_processed_Links_partial,
        auto_ack=False
    )
    # Add Links To Crawl Schedule
    queue_service._channel.basic_consume(
        queue=DbWriterQueueChannels.ADD_LINKS_TO_SCHEDULE,
        on_message_callback=add_links_to_schedule_partial,
        auto_ack=False
    )

    logger.info("Listening for Database requests...")
    queue_service._channel.start_consuming()

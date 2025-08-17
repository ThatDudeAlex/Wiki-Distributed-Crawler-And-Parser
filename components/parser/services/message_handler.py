import logging
import os
from functools import partial
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.parsing import ParsingTask
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from components.parser.services.parsing_service import ParsingService
from components.parser.monitoring.metrics import (
    PARSER_MESSAGES_RECEIVED_TOTAL,
    PARSER_MESSAGE_FAILURES_TOTAL,
    STAGE_DURATION_SECONDS,
)


def handle_parsing_message(ch, method, properties, body, parsing_service: ParsingService, logger: logging.Logger):
    """
    Callback function for handling incoming parsing tasks from the queue

    Decodes the incoming message, validates it, and triggers the parsing pipeline
    """
    try:
        message_str = body.decode('utf-8')
        task = ParsingTask.model_validate_json(message_str)

        if not os.path.exists(task.compressed_filepath):
            logger.warning("Compressed HTML file not found: %s", task.compressed_filepath)
            PARSER_MESSAGES_RECEIVED_TOTAL.labels(status="missing_file").inc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        with STAGE_DURATION_SECONDS.labels("total_latency").time():
            logger.info("Initiating parsing on file: %s", task.compressed_filepath)
            parsing_service.run(task)

        PARSER_MESSAGES_RECEIVED_TOTAL.labels(status="valid").inc()

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except ValueError as e:
        logger.error("Message skipped - invalid ParsingTask: %s", e)
        PARSER_MESSAGES_RECEIVED_TOTAL.labels(status="invalid").inc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        error_type = type(e).__name__
        logger.exception("Unexpected error while processing message")
        PARSER_MESSAGE_FAILURES_TOTAL.labels(error_type=error_type).inc()
        PARSER_MESSAGES_RECEIVED_TOTAL.labels(status="error").inc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        


def start_parser_listener(queue_service: QueueService, parsing_service: ParsingService, logger: logging.Logger):
    """
    Starts the message listener for incoming parsing tasks

    Uses RabbitMQ's basic_consume to listen on the `pages_to_parse` queue,
    and routes each message to the `handle_parsing_message` function via `partial`
    """
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the parser & logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_message_partial = partial(
        handle_parsing_message, parsing_service=parsing_service, logger=logger
    )

    queue_service._channel.basic_consume(
        queue=ParserQueueChannels.PAGES_TO_PARSE.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for parsing requests...")
    queue_service._channel.start_consuming()

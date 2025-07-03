import json
import logging
from functools import partial
import os
from components.parser.services.parsing_service import ParsingService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.enums.queue_names import ParserQueueChannels


def handle_message(ch, method, properties, body, parsing_service: ParsingService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = ParsingTask(**message_dict)
        task.validate_consume()

        if not os.path.exists(task.compressed_filepath):
            logger.warning("File does not exist: %s", task.compressed_filepath)

        logger.info("Initiating parsing on file: %s", task.compressed_filepath)
        parsing_service.run(task)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e.json())
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_parser_listener(queue_service: QueueService, parsing_service: ParsingService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the parser & logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_message_partial = partial(
        handle_message, parsing_service=parsing_service, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=ParserQueueChannels.LISTEN.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for parsing requests...")
    queue_service.channel.start_consuming()

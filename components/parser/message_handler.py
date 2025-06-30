import json
import logging
from functools import partial
from components.parser.services.parsing_service import ParsingService
from shared.queue_service import QueueService
from shared.message_schemas.parse_task_schemas import ParsingTaskSchema
from components.parser.configs.app_configs import PARSER_QUEUE_CHANNELS


def handle_message(ch, method, properties, body, parsing_service: ParsingService, logger: logging.Logger):
    try:
        message = json.loads(body.decode())
        task = ParsingTaskSchema(**message)

        logger.info("Initiating parsing on file: %s", task.compressed_path)

        # TODO: experiment with removing str()
        parsing_service.run(str(task.url), task.compressed_path)

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
        queue=PARSER_QUEUE_CHANNELS['listen'],
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for parsing requests...")
    queue_service.channel.start_consuming()

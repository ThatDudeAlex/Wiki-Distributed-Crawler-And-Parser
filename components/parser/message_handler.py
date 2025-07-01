import json
import logging
from functools import partial
from components.parser.services.parsing_service import ParsingService
from rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.rabbitmq.enums.queue_names import ParserQueueChannels


def handle_message(ch, method, properties, body, parsing_service: ParsingService, logger: logging.Logger):
    try:
        message = json.loads(body.decode())
        task = ParsingTask.model_validate_json(message)

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
        queue=ParserQueueChannels.LISTEN.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for parsing requests...")
    queue_service.channel.start_consuming()

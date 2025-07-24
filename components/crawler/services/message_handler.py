import json
import logging
from functools import partial

from pydantic import ValidationError
from components.crawler.services.crawler_service import CrawlerService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels


def handle_crawl_message(ch, method, properties, body, crawler_service: CrawlerService, logger: logging.Logger):
    """
    Callback function for handling incoming crawl tasks from the queue

    Decodes the message body, validates it into a CrawlTask, and passes it to the CrawlerService.
    Acknowledges successful processing or rejects invalid/failed tasks
    """
    try:
        task = parse_crawl_task(body)

        logger.info("Initiating crawl for URL: %s", task.url)
        crawler_service.run(task)

        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except UnicodeDecodeError as e:
        logger.error("Failed to decode message body as UTF-8: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except ValidationError as e:
        logger.error("Message failed schema validation: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        logger.exception("Unexpected error processing message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def parse_crawl_task(body: bytes) -> CrawlTask:
    """
    Decode and validate a raw RabbitMQ message into a CrawlTask object

    Args:
        body (bytes): Raw message body from RabbitMQ

    Returns:
        CrawlTask: Parsed and validated crawl task object

    Raises:
        UnicodeDecodeError: If the message body is not valid UTF-8
        pydantic.ValidationError: If the decoded JSON does not match the CrawlTask schema
    """
    message_str = body.decode("utf-8")
    return CrawlTask.model_validate_json(message_str)


def start_crawler_listener(queue_service: QueueService, crawler_service: CrawlerService, logger: logging.Logger):
    """
    Starts the message listener for incoming crawl tasks

    Uses RabbitMQ's basic_consume to listen on the `urls_to_crawl` queue,
    and routes each message to the `handle_crawl_message` function via `partial`
    """

    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the crawler & logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_message_partial = partial(
        handle_crawl_message, crawler_service=crawler_service, logger=logger
    )

    queue_service._channel.basic_consume(
        queue=CrawlerQueueChannels.URLS_TO_CRAWL.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service._channel.start_consuming()

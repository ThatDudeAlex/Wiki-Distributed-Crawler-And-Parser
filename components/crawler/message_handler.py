from functools import partial
import json
import logging
from components.crawler.configs.types import CrawlTask
from components.crawler.services.crawler_service import CrawlerService
from shared.queue_service import QueueService
from shared.config import CRAWLER_QUEUE_CHANNELS


def handle_message(ch, method, properties, body, crawler_service: CrawlerService, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())
        task = CrawlTask(**message)

        # run crawler service
        crawler_service.run(task.url, task.depth)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e.json())
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # TODO: look into if retrying could help the situation
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_crawl_listener(queue_service: QueueService, crawler_service: CrawlerService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the crawler & logger while still complying with
    # the RabbitMQ api for listening to messages
    handler = partial(
        handle_message, crawler_service=crawler_service, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=CRAWLER_QUEUE_CHANNELS['listen'],
        on_message_callback=handler,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service.channel.start_consuming()

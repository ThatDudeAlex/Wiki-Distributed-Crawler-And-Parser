from functools import partial
import json
import logging
from components.crawler.services.crawler_service import CrawlerService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels


def handle_message(ch, method, properties, body, crawler_service: CrawlerService, logger: logging.Logger):
    try:
        # model_validate_json(body)
        task = CrawlTask.model_validate_json(body)

        logger.info("Initiating crawl for URL: %s", task.url)

        # run crawler service
        # IMPORTANT: url must be converted to a string to avoid potential type errors
        # TODO: idk how true is the important comment above, experiment with removing str()
        crawler_service.run(str(task.url), task.depth)

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
    handle_message_partial = partial(
        handle_message, crawler_service=crawler_service, logger=logger
    )

    queue_service.channel.basic_consume(
        queue=CrawlerQueueChannels.LISTEN.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service.channel.start_consuming()

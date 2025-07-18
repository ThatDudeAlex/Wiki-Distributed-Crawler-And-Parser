from functools import partial
import json
import logging
from components.crawler.services.crawler_service import CrawlerService
from shared.rabbitmq.queue_service import QueueService
# from shared.rabbitmq.schemas.crawling_task_schemas import CrawlTask, ValidationError
from shared.rabbitmq.schemas.crawling import CrawlTask
from shared.rabbitmq.enums.queue_names import CrawlerQueueChannels


def run_crawler(ch, method, properties, body, crawler_service: CrawlerService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        task = CrawlTask.model_validate_json(message_str)

        logger.info("Initiating crawl for URL: %s", task.url)
        crawler_service.run(task)

        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # except ValidationError as e:
    #     logger.error("Validation failed: %s", str(e))
    #     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON format: %s", str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception:
        logger.exception("Unexpected error processing message:")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_crawler_listener(queue_service: QueueService, crawler_service: CrawlerService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the crawler & logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_message_partial = partial(
        run_crawler, crawler_service=crawler_service, logger=logger
    )

    queue_service._channel.basic_consume(
        queue=CrawlerQueueChannels.URLS_TO_CRAWL.value,
        on_message_callback=handle_message_partial,
        auto_ack=False
    )

    logger.info("Listening for crawl requests...")
    queue_service._channel.start_consuming()

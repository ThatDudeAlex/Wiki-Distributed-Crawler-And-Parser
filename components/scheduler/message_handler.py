from functools import partial
import json
import logging
from pydantic import TypeAdapter
from shared.rabbitmq.queue_service import QueueService
from components.scheduler.configs.app_configs import SCHEDULER_QUEUE_CHANNELS
from shared.rabbitmq.schemas.crawling_task_schemas import CrawlReport, FailedCrawlReport, SuccessCrawlReport

ReportAdapter = TypeAdapter(CrawlReport)


def handle_crawl_result_message(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        # Validate and convert the message using TypeAdapter
        report = ReportAdapter.validate_python(message)

        if isinstance(report, SuccessCrawlReport):
            handle_success(report, logger)
        elif isinstance(report, FailedCrawlReport):
            handle_failure(report, logger)

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


def handle_process_links_message(ch, method, properties, body, logger: logging.Logger):
    try:
        logger.debug("Received message: %s", body)
        message = json.loads(body.decode())

        # TODO: Implement
        # save_report_page_content(message, logger)

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


def start_schedule_listener(queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    handle_save_page_partial = partial(
        handle_process_links_message, logger=logger
    )
    handle_save_page_content_partial = partial(
        handle_process_links_message, logger=logger
    )

    # listen for crawl results
    queue_service.channel.basic_consume(
        queue=SCHEDULER_QUEUE_CHANNELS.crawlresult,
        on_message_callback=handle_save_page_partial,
        auto_ack=False
    )
    # listen for link processing
    queue_service.channel.basic_consume(
        queue=SCHEDULER_QUEUE_CHANNELS.processlinks,
        on_message_callback=handle_save_page_content_partial,
        auto_ack=False
    )

    logger.info("Scheduler is listerning...")
    queue_service.channel.start_consuming()

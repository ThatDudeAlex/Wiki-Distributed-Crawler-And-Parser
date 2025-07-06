from functools import partial
import json
import logging
from components.scheduler.services.schedule_service import ScheduleService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks


def process_discovered_links(ch, method, properties, body, scheduler: ScheduleService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = ProcessDiscoveredLinks(**message_dict)
        task.validate_consume()

        scheduler.process_links(task)

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


def start_schedule_listener(scheduler_service: ScheduleService, queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    process_discovered_links_partial = partial(
        process_discovered_links, scheduler=scheduler_service, logger=logger
    )

    # listen for crawl results
    queue_service.channel.basic_consume(
        queue=SchedulerQueueChannels.LINKS_TO_SCHEDULE.value,
        on_message_callback=process_discovered_links_partial,
        auto_ack=False
    )

    logger.info("Scheduler is listerning...")
    queue_service.channel.start_consuming()

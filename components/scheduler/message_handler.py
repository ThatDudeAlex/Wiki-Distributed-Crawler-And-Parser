from functools import partial
import json
import logging
from components.scheduler.services.schedule_service import ScheduleService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks


def links_to_schedule(ch, method, properties, body, scheduler: ScheduleService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = ProcessDiscoveredLinks(**message_dict)
        task.validate_consume()

        scheduler.schedule_links(task)

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


def scheduled_links_to_process(ch, method, properties, body, scheduler: ScheduleService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        message_dict = json.loads(message_str)

        task = ProcessDiscoveredLinks(**message_dict)
        task.validate_consume()

        # logger.info('GOT FROM LEAKY BUCKET: %s', link.url)

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
    links_to_schedule_partial = partial(
        links_to_schedule, scheduler=scheduler_service, logger=logger
    )

    scheduled_links_to_process_partial = partial(
        scheduled_links_to_process, scheduler=scheduler_service, logger=logger
    )

    # listen for links to schedule
    queue_service._channel.basic_consume(
        queue=SchedulerQueueChannels.LINKS_TO_SCHEDULE.value,
        on_message_callback=links_to_schedule_partial,
        auto_ack=False
    )
    # listen for scheduled links to process
    queue_service._channel.basic_consume(
        queue=SchedulerQueueChannels.SCHEDULED_LINKS_TO_PROCESS.value,
        on_message_callback=scheduled_links_to_process_partial,
        auto_ack=False
    )

    logger.info("Scheduler is listerning...")
    queue_service._channel.start_consuming()

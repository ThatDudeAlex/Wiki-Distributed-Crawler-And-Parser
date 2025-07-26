from functools import partial
import logging
from components.scheduler.services.schedule_service import ScheduleService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.scheduling import ProcessDiscoveredLinks


def links_to_schedule(ch, method, properties, body, scheduler: ScheduleService, logger: logging.Logger):
    try:
        message_str = body.decode('utf-8')
        task = ProcessDiscoveredLinks.model_validate_json(message_str)

        scheduler.process_links(task)

        # acknowledge success
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        # TODO: look into if retrying could help the situation
        # maybe requeue for OperationalError or add a dead-letter queue
        logger.exception("Unexpected error processing links to schedule")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_schedule_listener(scheduler_service: ScheduleService, queue_service: QueueService, logger: logging.Logger):
    # Partial allows us to inject the value of a param into a function
    # This allows me to inject the logger while still complying with
    # the RabbitMQ api for listening to messages
    links_to_schedule_partial = partial(
        links_to_schedule, scheduler=scheduler_service, logger=logger
    )

    # listen for links to schedule
    queue_service._channel.basic_consume(
        queue=SchedulerQueueChannels.LINKS_TO_SCHEDULE.value,
        on_message_callback=links_to_schedule_partial,
        auto_ack=False
    )

    logger.info("Scheduler is listerning...")
    queue_service._channel.start_consuming()

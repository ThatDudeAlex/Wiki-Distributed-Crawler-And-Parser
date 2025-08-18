"""
Message handler for the Scheduler component.

Defines the consumer callback for processing discovered links and sets up
the RabbitMQ listener to receive scheduling tasks.
"""

import logging
from functools import partial

from components.scheduler.monitoring.metrics import SCHEDULER_MESSAGE_FAILURES_TOTAL, SCHEDULER_MESSAGES_RECEIVED_TOTAL, SCHEDULER_PROCESSING_DURATION_SECONDS
from components.scheduler.services.schedule_service import ScheduleService
from shared.rabbitmq.queue_service import QueueService
from shared.rabbitmq.enums.queue_names import SchedulerQueueChannels
from shared.rabbitmq.schemas.scheduling import ProcessDiscoveredLinks


def links_to_schedule(ch, method, properties, body, scheduler: ScheduleService, logger: logging.Logger):
    """
    Callback function to handle incoming scheduling messages

    Decodes the message, validates it as a ProcessDiscoveredLinks task,
    and forwards it to the scheduler for processing

    Acknowledges or rejects the message based on processing outcome
    """
    try:
        message_str = body.decode('utf-8')
        task = ProcessDiscoveredLinks.model_validate_json(message_str)

        with SCHEDULER_PROCESSING_DURATION_SECONDS.labels("total_latency").time():
            scheduler.process_links(task)

        SCHEDULER_MESSAGES_RECEIVED_TOTAL.labels(status="valid").inc()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except ValueError as e:
        logger.error("Message Skipped - Invalid task message: %s", e)
        SCHEDULER_MESSAGE_FAILURES_TOTAL.labels(error_type="ValueError").inc()
        SCHEDULER_MESSAGES_RECEIVED_TOTAL.labels(status="error").inc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception:
        # TODO: Requeue only on transient errors (e.g., database OperationalError)
        #       Consider adding dead-letter queue handling for persistent failures
        logger.exception("Unexpected error processing links to schedule")
        SCHEDULER_MESSAGE_FAILURES_TOTAL.labels(error_type="ValueError").inc()
        SCHEDULER_MESSAGES_RECEIVED_TOTAL.labels(status="error").inc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_schedule_listener(scheduler_service: ScheduleService, queue_service: QueueService, logger: logging.Logger):
    """
    Initializes RabbitMQ consumer for scheduling messages.

    Binds the `links_to_schedule` callback with the required scheduler service
    and logger, and begins consuming messages from the relevant queue.
    """
    links_to_schedule_partial = partial(
        links_to_schedule, scheduler=scheduler_service, logger=logger
    )

    # TODO: Replace direct access to _channel with a public consume method on QueueService
    queue_service._channel.basic_consume(
        queue=SchedulerQueueChannels.LINKS_TO_SCHEDULE.value,
        on_message_callback=links_to_schedule_partial,
        auto_ack=False
    )

    logger.info("Scheduler is listening for scheduling messages...")
    queue_service._channel.start_consuming()

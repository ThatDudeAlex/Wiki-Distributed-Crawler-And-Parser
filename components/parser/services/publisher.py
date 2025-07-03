from datetime import datetime
import logging
from typing import List
from shared.rabbitmq.schemas.parsing_task_schemas import ParsedContent, LinkData
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import ProcessDiscoveredLinks
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_parsed_data(self, page_content: ParsedContent):
        message = page_content
        message.validate_publish()

        self._queue_service.publish(
            ParserQueueChannels.SAVE_PARSED_DATA.value, message)

        self._logger.info("Published: Save Parsed Data")

    # TODO: Implement retry mechanism and dead-letter
    def publish_process_links_task(self, page_links: List[LinkData]):

        message = ProcessDiscoveredLinks(links=page_links)
        message.validate_publish()

        self._queue_service.publish(
            ParserQueueChannels.PROCESS_LINKS.value, message)

        self._logger.debug("Published: Process Links")

import logging
from typing import List
from shared.rabbitmq.schemas.save_to_db import SaveParsedContent
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.schemas.scheduling import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_parsed_data(self, page_content: SaveParsedContent):
        message = page_content

        self._queue_service.publish(
            ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value, message.model_dump_json())

        self._logger.info("Published: Save Parsed Data")

    # TODO: Implement retry mechanism and dead-letter
    def publish_process_links_task(self, page_links: List[LinkData]):

        message = ProcessDiscoveredLinks(links=page_links)

        self._queue_service.publish(
            ParserQueueChannels.LINKS_TO_SCHEDULE.value, message.model_dump_json())

        self._logger.debug("Published: Process Links")

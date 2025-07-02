from datetime import datetime
import logging
from typing import List
from components.parser.configs.types import LinkData, PageContent
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.schemas.parsing_task_schemas import DiscoveredLinkPydanticModel, ProcessDiscoveredLinksMsg
from shared.rabbitmq.queue_service import QueueService


class PublishingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    # TODO: Implement retry mechanism and dead-letter
    def publish_save_parsed_data(self, page_content: PageContent):
        message = page_content.to_parsed_contents_message().model_dump_json()

        self._queue_service.publish(
            ParserQueueChannels.SAVE_PARSED_DATA.value, message)

        self._logger.info("Published: Save Parsed Data")

    # TODO: Implement retry mechanism and dead-letter
    def publish_process_links_task(self, url: str, discovered_at: datetime, page_links: List[LinkData]):

        # Convert the list using a list comprehension
        page_links: List[DiscoveredLinkPydanticModel] = [
            link.to_discovered_link() for link in page_links
        ]

        message = ProcessDiscoveredLinksMsg(
            source_page_url=url, discovered_at=discovered_at, links=page_links
        ).model_dump_json()

        self._queue_service.publish(
            ParserQueueChannels.PROCESS_LINKS.value, message)

        self._logger.debug("Published: Process Links")

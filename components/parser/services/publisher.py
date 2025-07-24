import logging
from typing import List
from components.parser.core.metrics import PUBLISHED_MESSAGES_TOTAL
from shared.rabbitmq.schemas.save_to_db import SaveParsedContent
from shared.rabbitmq.enums.queue_names import ParserQueueChannels
from shared.rabbitmq.schemas.scheduling import LinkData, ProcessDiscoveredLinks
from shared.rabbitmq.queue_service import QueueService



class PublishingService:
    """
    Responsible for publishing processed parsing data to the appropriate queues
    """

    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger


    def publish_save_parsed_data(self, page_content: SaveParsedContent):
        """
        Publishes the extracted page content to the 'parsed_content_to_save' queue

        Args:
            page_content (SaveParsedContent): Parsed page content to persist
        """
        try:
            message = page_content

            self._queue_service.publish(
                ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value, message.model_dump_json())
            
            self._logger.info("Published SaveParsedContent for URL: %s", page_content.url)
            PUBLISHED_MESSAGES_TOTAL.labels(
                queue=ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value,
                status="success"
            ).inc()
            
        except Exception as e:
            self._logger.exception("Failed to publish SaveParsedContent: %s", e)
            PUBLISHED_MESSAGES_TOTAL.labels(
                queue=ParserQueueChannels.PARSED_CONTENT_TO_SAVE.value,
                status="failure"
            ).inc()
            # TODO: implement retry or move to dead-letter queue


    def publish_process_links_task(self, page_links: List[LinkData]):
        """
        Publishes a list of extracted links to the scheduler queue

        Args:
            page_links (List[LinkData]): List of discovered links on the page
        """
        try:
            message = ProcessDiscoveredLinks(links=page_links)

            self._queue_service.publish(
                ParserQueueChannels.LINKS_TO_SCHEDULE.value, message.model_dump_json())

            self._logger.info("Published: %d Process Links To Process", len(page_links))
            PUBLISHED_MESSAGES_TOTAL.labels(
                queue=ParserQueueChannels.LINKS_TO_SCHEDULE.value,
                status="success"
            ).inc()

        except Exception as e:
            self._logger.exception("Failed to publish ProcessDiscoveredLinks task: %s", e)
            PUBLISHED_MESSAGES_TOTAL.labels(
                queue=ParserQueueChannels.LINKS_TO_SCHEDULE.value,
                status="failure"
            ).inc()
            # TODO: implement retry or move to dead-letter queue

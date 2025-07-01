import logging
from typing import List
from components.parser.configs.types import LinkData, PageContentSchema
from rabbitmq.queue_service import QueueService
from components.parser.core.wiki_content_extractor import extract_wiki_page_content
from components.parser.core.wiki_link_extractor import extract_wiki_page_links
from components.parser.services.compressed_html_reader import load_compressed_html
from shared.rabbitmq.enums.queue_names import ParserQueueChannels


class ParsingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        pass

    def run(self, url: str, compressed_path: str):
        try:
            self._logger.info(
                'STAGE 1: Loading HTML file from: %s', compressed_path
            )
            html_content = load_compressed_html(compressed_path, self._logger)

            if html_content is None:
                self._logger.error(
                    "Skipping Parsing Task - Html content did not load"
                )
                return

            self._logger.info('STAGE 2: Extracting Page Content')
            page_content = extract_wiki_page_content(
                url, html_content, self._logger)

            self._logger.info('STAGE 3: Extracting Links')
            page_links = extract_wiki_page_links(
                url, html_content, self._logger)

            self._logger.info('STAGE 4: Publish Save Page Content')
            self._send_save_parsed_data_message(page_content)

            self._logger.info('STAGE 5: Publish Process Links')
            self._send_process_links_message(page_links)

            self._logger.info('Parsing Task Successfully Completed!')
        except Exception as e:
            exception_type_name = type(e).__name__
            self._logger.error(
                f"An exception of type '{exception_type_name}' occurred: {e}")
            return

    # TODO: Implement retry mechanism and dead-letter
    def _send_save_parsed_data_message(self, page_content: PageContentSchema):
        self._queue_service.publish(
            ParserQueueChannels.SAVE_PARSED_DATA.value, page_content.model_dump(mode="json"))

        self._logger.debug(f"Task Published - Save Page Content")

    # TODO: Implement retry mechanism and dead-letter
    def _send_process_links_message(self, page_links: List[LinkData]):

        message = [link.model_dump(mode="json") for link in page_links]

        self._queue_service.publish(
            ParserQueueChannels.PROCESS_LINKS.value, message)

        self._logger.debug(f"Task Published - Process Links")

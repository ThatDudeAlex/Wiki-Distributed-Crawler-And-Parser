import logging
from shared.rabbitmq.queue_service import QueueService
from components.parser.core.wiki_content_extractor import extract_wiki_page_content
from components.parser.core.wiki_link_extractor import extract_wiki_page_links
from components.parser.services.compressed_html_reader import load_compressed_html
from components.parser.services.publisher import PublishingService
from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask
from shared.utils import get_timestamp_eastern_time


class ParsingService:
    def __init__(self, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        self._publisher = PublishingService(self._queue_service, self._logger)
        pass

    def run(self, task: ParsingTask):
        url = task.url
        depth = task.depth
        compressed_filepath = task.compressed_filepath

        try:
            self._logger.info(
                'STAGE 1: Loading HTML file from: %s', compressed_filepath
            )
            html_content = load_compressed_html(
                compressed_filepath, self._logger)

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
                url, html_content, depth, self._logger)

            parsed_at = get_timestamp_eastern_time()

            self._logger.info('STAGE 4: Publish Save Page Content')
            # self._send_save_parsed_data_message(page_content)
            self._publisher.publish_save_parsed_data(page_content)

            self._logger.info('STAGE 5: Publish Process Links')
            # self._send_process_links_message(page_links)
            self._publisher.publish_process_links_task(
                url, parsed_at, page_links)

            self._logger.info('Parsing Task Successfully Completed!')
        except Exception as e:
            exception_type_name = type(e).__name__
            self._logger.error(
                f"An exception of type '{exception_type_name}' occurred: {e}")
            return

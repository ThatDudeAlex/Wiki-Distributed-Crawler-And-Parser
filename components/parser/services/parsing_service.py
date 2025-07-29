import logging
from typing import Any
from shared.rabbitmq.queue_service import QueueService
from components.parser.core.wiki_content_extractor import PageContentExtractor
from components.parser.core.wiki_link_extractor import PageLinkExtractor
from components.parser.services.compressed_html_reader import load_compressed_html
from components.parser.services.publisher import PublishingService
from shared.rabbitmq.schemas.parsing import ParsingTask
from components.parser.monitoring.metrics import PAGES_PARSED_TOTAL, LINKS_EXTRACTED_TOTAL, STAGE_DURATION_SECONDS


class ParsingService:
    """
    Orchestrates the parsing workflow for a given task

    This includes:
        - Loading and decompressing HTML content from file
        - Extracting structured page content
        - Extracting hyperlinks to schedule
        - Publishing parsed content and links to the appropriate queues
    """

    def __init__(self, configs: dict[str, Any], queue_service: QueueService, logger: logging.Logger):
        """
        Initializes the ParsingService

        Args:
            configs (dict): Configuration dictionary for extractors
            queue_service (QueueService): RabbitMQ interface for publishing results
            logger (logging.Logger): Logger instance
        """
        self._queue_service = queue_service
        self._logger = logger
        self.content_extractor = PageContentExtractor(configs, logger)
        self.link_extractor = PageLinkExtractor(configs, logger)
        self._publisher = PublishingService(self._queue_service, logger)

    def run(self, task: ParsingTask):
        """
        Executes the full parsing pipeline for a single task.

        Steps:
            1. Load compressed HTML from disk
            2. Extract structured content and links
            3. Publish parsed content to be saved
            4. Publish extracted links for scheduling

        Args:
            task (ParsingTask): The parsing task containing URL, depth, and file path.
        """
        url = task.url
        depth = task.depth
        filepath = task.compressed_filepath

        try:
            with STAGE_DURATION_SECONDS.labels("load_html").time():
                self._logger.info(
                    'STAGE 1: Loading HTML file from: %s', filepath)
                html_content = load_compressed_html(filepath, self._logger)

                if html_content is None:
                    self._logger.error("Skipping Parsing Task - HTML content could not be loaded")
                    return

            with STAGE_DURATION_SECONDS.labels("extract_content").time():
                self._logger.info('STAGE 2: Extracting Page Content')
                page_content = self.content_extractor.extract(url, html_content)

            with STAGE_DURATION_SECONDS.labels("extract_links").time():
                self._logger.info('STAGE 3: Extracting Links')
                page_links = self.link_extractor.extract(url, html_content, depth)
                LINKS_EXTRACTED_TOTAL.inc(len(page_links))

            with STAGE_DURATION_SECONDS.labels("publish_content").time():
                self._logger.info('STAGE 4: Publish Save Page Content')
                self._publisher.publish_save_parsed_data(page_content)

            with STAGE_DURATION_SECONDS.labels("publish_links").time():
                self._logger.info('STAGE 5: Publish Process Links')
                self._publisher.publish_process_links_task(page_links)

            self._logger.info('Parsing Task Completed for URL: %s', url)

        except Exception:
            self._logger.exception("Unexpected error during parsing task for %s", url)
            # TODO: Consider sending failed parsing task to DLQ

        finally:
            PAGES_PARSED_TOTAL.inc()

import logging
from shared.rabbitmq.queue_service import QueueService
from components.parser.core.wiki_content_extractor import PageContentExtractor
from components.parser.core.wiki_link_extractor import PageLinkExtractor
from components.parser.services.compressed_html_reader import load_compressed_html
from components.parser.services.publisher import PublishingService
from shared.rabbitmq.schemas.parsing import ParsingTask
# from shared.rabbitmq.schemas.parsing_task_schemas import ParsingTask

from components.parser.core.metrics import PAGES_PARSED_TOTAL, LINKS_EXTRACTED_TOTAL, STAGE_DURATION_SECONDS


class ParsingService:
    def __init__(self, configs, queue_service: QueueService, logger: logging.Logger):
        self._queue_service = queue_service
        self._logger = logger
        self.content_extractor = PageContentExtractor(
            configs.selectors, logger)
        self.link_extractor = PageLinkExtractor(
            configs.selectors, logger
        )
        self._publisher = PublishingService(self._queue_service, logger)

    def run(self, task: ParsingTask):
        url = task.url
        depth = task.depth
        filepath = task.compressed_filepath

        try:
            with STAGE_DURATION_SECONDS.labels("load_html").time():
                self._logger.info(
                    'STAGE 1: Loading HTML file from: %s', filepath)
                html_content = load_compressed_html(filepath, self._logger)

                if html_content is None:
                    self._logger.error(
                        "Skipping Parsing Task - Html content did not load"
                    )
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

            self._logger.info('Parsing Task Successfully Completed!')
        except Exception as e:
            exception_type_name = type(e).__name__
            self._logger.error(
                f"An exception of type '{exception_type_name}' occurred: {e}")
            return
        finally:
            PAGES_PARSED_TOTAL.inc()
            pass

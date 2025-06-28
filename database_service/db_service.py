import json
import logging
import os

from dotenv import load_dotenv
from database.db_models.models import Page, Link, PageContent, Category, CrawlStatus
from database.engine import SessionLocal
from shared.logger import setup_logging
from shared.queue_service import QueueService
from shared.config import DB_SERVICE_QUEUE_CHANNELS

MAX_RETRIES = 3


class DatabaseService:
    def __init__(self):
        load_dotenv()
        self._logger = setup_logging(
            os.getenv('DB_SERVICE_LOGS', 'logs/db_service.log')
        )

        # DB connection setup
        self._db = SessionLocal()

        # rabbitMQ setup
        self.queue = QueueService(
            self._logger,
            list(DB_SERVICE_QUEUE_CHANNELS.values())
        )
        self.queue.channel.basic_consume(
            queue=DB_SERVICE_QUEUE_CHANNELS['savepage'],
            on_message_callback=self._consume_save_page_msg,
            auto_ack=False
        )
        self.queue.channel.basic_consume(
            queue=DB_SERVICE_QUEUE_CHANNELS['savecontent'],
            on_message_callback=self._consume_save_parsed_content_msg,
            auto_ack=False
        )

    def _consume_save_page_msg(self, ch, method, properties, body):
        try:
            # Process the message
            message = json.loads(body.decode())
            self._save_crawled_page(message)

            self._logger.info(
                f"Processed request to save URL: {message['url']}")

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _consume_save_parsed_content_msg(self, ch, method, properties, body):
        try:
            # Process the message
            message = json.loads(body.decode())
            self._save_crawled_page(message)

            self._logger.info(f"Processed request to save parsed content")

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _save_crawled_page(self, page_data: dict):
        r"""Adds a new ``Page`` into the database

        :param crawl_data: Tuple containing ``(url, url_hash, filepath, status_code)``
        """
        for i in range(1, 4):
            try:
                page = Page(
                    url=page_data['url'],
                    url_hash=page_data['url_hash'],
                    last_crawl_status=CrawlStatus.CRAWLED_SUCCESS,
                    http_status_code=page_data['status_code'],
                    compressed_path=page_data['compressed_path'])
                self._db.add(page)
                self._db.commit()
                self._logger.debug(
                    f"Success: Page '{page_data['url']}' was saved into the database")
                return
            except Exception as e:
                self._logger.warning(
                    f"Failed to saved crawled page - Attempt {i}/{MAX_RETRIES} - Url: {page_data['url']}")
                self._logger.warning(
                    f"Error encountered while saving page: {page_data['url']} - {e}")

        self._logger.error(f"Page '{page_data['url']}' failed to be saved")

    def save_parsed_page(self, parsed_data: dict):
        r"""Adds a new ``page_content`` entry into the database"""

        page_content = PageContent(
            url=parsed_data['page_url'],
            title=parsed_data['title'],
            summary=parsed_data['summary'],
            content=parsed_data['content']
        )
        self._db.add(page_content)
        self._db.commit()

    # def save_category(self, name):
    #     category = Category(
    #         name=name
    #     )
    #     self._db.add(category)
    #     self._db.commit()
    #     return True

    # def _save_uncrawled_page(self, url: str, crawl_status: CrawlStatus, status_code: int) -> int:
    #     page = Page(
    #         url=url,
    #         last_crawl_status=crawl_status,
    #         http_status_code=status_code,
    #     )
    #     self._db.add(page)
    #     self._db.commit()
    #     return page.id

    # def save_skipped_page(self, url: str, status_code: int) -> int:
    #     r"""Adds a page with ``CrawlStatus.SKIPPED`` into the database. Returns ``page_id``

    #     :param url: the ``url`` of the page being skipped

    #     :param status_code: the ``HTTP Status Code`` of the request
    #     """
    #     return self._save_uncrawled_page(url, CrawlStatus.SKIPPED, status_code)

    # def save_failed_page_crawl(self, url: str, status_code: int) -> int:
    #     r"""Adds a page with ``CrawlStatus.CRAWL_FAILED`` into the database. Returns ``page_id``

    #     :param url: the ``url`` of the page that failed to be crawl

    #     :param status_code: the ``HTTP Status Code`` of the failed request
    #     """
    #     return self._save_uncrawled_page(url, CrawlStatus.CRAWL_FAILED, status_code)

    # def save_link(self, page_id, target_url, is_internal=False):
    #     link = Link(
    #         source_page_id=page_id,
    #         target_url=target_url,
    #         is_internal=is_internal
    #     )
    #     self._db.add(link)
    #     self._db.commit()


if __name__ == "__main__":
    service = DatabaseService()
    service.queue.channel.start_consuming()

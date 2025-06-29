import json

from dotenv import load_dotenv
from database.db_models.models import Page, Link, PageContent, Category, CrawlStatus
from database.engine import SessionLocal
from shared.logging_utils import get_logger
from shared.queue_service import QueueService
from shared.config import DB_SERVICE_QUEUE_CHANNELS

MAX_RETRIES = 3


class DatabaseService:
    def __init__(self):
        load_dotenv()
        self._logger = get_logger('DB_Service')

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
            # TODO: implement retries and set requeue to true
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _consume_save_parsed_content_msg(self, ch, method, properties, body):
        try:
            # Process the message
            message = json.loads(body.decode())
            self.save_parsed_page(message)

            self._logger.info(f"Processed request to save parsed content")

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            # TODO: implement retries and set requeue to true
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

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
            page_url=parsed_data['page_url'],
            title=parsed_data['title'],
            summary=parsed_data['summary'],
            content=parsed_data['content']
        )
        self._db.add(page_content)
        self._db.commit()


if __name__ == "__main__":
    service = DatabaseService()
    service.queue.channel.start_consuming()

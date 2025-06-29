import json

from bs4 import BeautifulSoup
from shared.logging_utils import get_logger
from shared.queue_service import QueueService
from shared.db_service import DatabaseService
from shared.config import PARSER_QUEUE_CHANNELS
from .compress_html_handler import CompressFileHandler


class HtmlParser:
    def __init__(self):
        self._logger = get_logger('Parser')

        # rabbitMQ setup
        self.queue = QueueService(
            self._logger,
            list(PARSER_QUEUE_CHANNELS.values())
        )
        self.queue.channel.basic_consume(
            queue=PARSER_QUEUE_CHANNELS['listen'],
            on_message_callback=self._consume_rabbit_message,
            auto_ack=False
        )

        self.cmp_handler = CompressFileHandler(self._logger)

        # database setup
        self.db = DatabaseService(self._logger)

        self._logger.info('Parser Initiation Complete')

    def _consume_rabbit_message(self, ch, method, properties, body):
        try:
            # Process the message
            message = json.loads(body.decode())
            self._parse_pages(message['page_url'], message['compressed_path'])

            # Acknowledge only after success
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _publish_parsed_content(self, parsed_data):
        page_url, title, summary, categories, content = parsed_data

        payload = {
            "page_url": page_url,
            "title": title,
            "summary": summary,
            "content": content,
        }
        self.queue.publish(PARSER_QUEUE_CHANNELS['savecontent'], payload)
        self._logger.debug(f"Published to save parsed content")

    def _parse_pages(self, page_url: str, compressed_path: str):
        html_content = self.cmp_handler.load_compressed_html(compressed_path)
        page_content = self._extract_page_content(html_content, page_url)

        title, summary, categories, content = page_content

        self._publish_parsed_content(
            (page_url, title, summary, categories, content))

        # self.db.save_parsed_page(page_url, title, summary, content)

        # for category in categories:
        #     self.db.save_category(category)

    def _extract_page_content(self, html_content: str, page_url: str):
        soup = BeautifulSoup(html_content, "lxml")
        title = self._extract_title(soup, page_url)
        self._logger.critical(f"title: {title}")
        summary = self._extract_summary(soup, page_url)
        categories = self._extract_categories(soup, page_url)
        content = self._extract_content(soup, page_url)
        return (title, summary, categories, content)

    def _extract_title(self, soup: BeautifulSoup, page_url: str) -> str:
        try:
            title = soup.find(id='firstHeading')
            self._logger.info(f"Found title for url: {page_url}")
            return title.get_text(strip=True)
        except Exception as e:
            self._logger.error(
                f"Error parsing title for url: {page_url}  -  error: {e}")
            return None

    def _extract_summary(self, soup: BeautifulSoup, page_url: str) -> str:
        try:

            # Get all paragraph elements under #mw-content-text
            paragraphs = soup.select('#mw-content-text p')
            first_paragraph = None

            for p in paragraphs:
                # Get the text content and strip whitespace (like spaces, newlines, tabs)
                # If the stripped text is not empty, this is our paragraph
                if p.get_text(strip=True):
                    first_paragraph = p
                    break

            if first_paragraph:
                self._logger.info(
                    f"Found page summary: {first_paragraph.text.strip()}")
                return first_paragraph.get_text(strip=True)

            self._logger.warning(
                f"Did not find summary for url: {page_url}")
            return first_paragraph
        except Exception as e:
            self._logger.error(
                f"Error parsing summary for url: {page_url}  -  error: {e}")
            return None

    def _extract_categories(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        try:

            # Get all paragraph elements under #mw-content-text
            category_links = soup.select('#mw-normal-catlinks li a')

            # Stores the text content
            category_texts = []

            for link in category_links:
                category_texts.append(link.get_text(strip=True))

            if not category_texts:
                self._logger.warning(
                    f"Did not find categories for url {page_url}")
                return None

            self._logger.info("Found the list of categories")
            return category_texts
        except Exception as e:
            self._logger.error(
                f"Error parsing summary for url: {page_url}  -  error: {e}")
            return None

    def _extract_content(self, soup: BeautifulSoup, page_url: str) -> str:
        try:

            content_div = soup.find('div', id='mw-content-text')

            if not content_div:
                self._logger.warning(
                    f"Main content div ('#mw-content-text') not found at - url: {page_url}")
                return None

            # Elements that are typically NOT part of the main text
            # These elements will be removed from the parsed content_div
            unwanted_selectors = [
                'div.toc',              # Table of Contents
                'div.hatnote',
                'sup.reference',        # Reference numbers/links ([1], [2])
                'span.mw-editsection',  # "edit" links next to section headings
                'table.infobox',        # Infoboxes
                'div.navbox',           # Navigation boxes
                'div.ambox',            # Article message boxes
                # Reference list section (the actual list of sources)
                'div.reflist',
                'ul.gallery',       # Image galleries
                # Indicators near the title (e.g., stability indicators)
                '.mw-indicators',
                'div.printfooter',    # Footer for printing
                'div.catlinks',       # Category links at the bottom
                '#siteSub',           # Subtitle for the site
                '#contentSub',        # Subtitle for the content
                '.mw-jump-link',      # "Jump to" links
                '.mw-cite-backlink',  # Backlinks from references
                '#column-one',        # Left sidebar
                '#mw-head'            # Top header
            ]

            # Remove the unwanted elements
            for selector in unwanted_selectors:
                for element in content_div.select(selector):
                    element.extract()  # Remove the tag and its contents

            text_elements = content_div.find_all(
                ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])

            article_text_parts = []
            for element in text_elements:
                text = element.get_text(separator=' ', strip=True)
                if text:  # Only add non-empty strings to avoid blank lines
                    article_text_parts.append(text)

            self._logger.info("Extracted the page content")

            # Join the collected text parts with double \n for better paragraph separation
            return '\n\n'.join(article_text_parts)

        except Exception as e:
            self._logger.error(
                f"Error parsing summary for url: {page_url}  -  error: {e}")
            return None


if __name__ == "__main__":
    parser = HtmlParser()
    parser.queue.channel.start_consuming()

import logging
from typing import List, Optional
from bs4 import BeautifulSoup, Tag

from shared.rabbitmq.schemas.parsing_task_schemas import ParsedContent
from components.parser.core.wiki_html_content_cleaner import clean_wiki_html_content
from shared.utils import create_hash, get_timestamp_eastern_time


class PageContentExtractor:
    def __init__(self, selectors, logger: logging.Logger):
        self.selectors = selectors
        self.logger = logger

    def extract(self, url: str, html_content: str) -> ParsedContent:
        """
        Parses HTML content from a Wikipedia-like page and returns structured content including
        title, categories, summary, main body text, and a hash of the text content.
        """
        soup = BeautifulSoup(html_content, "lxml")

        title = self._extract_title(soup)
        categories = self._extract_categories(soup)
        main_content = self._extract_main_body_content(soup)

        summary = None
        text_content = None
        text_content_hash = None

        if not main_content:
            self.logger.warning(
                'Failed to find main content — skipping summary & text_content')
        else:
            summary = self._extract_summary(main_content)
            text_content = clean_wiki_html_content(main_content, self.logger)
            text_content_hash = create_hash(text_content)

        parsed_at = get_timestamp_eastern_time()
        return ParsedContent(
            source_page_url=url,
            title=title,
            categories=categories,
            summary=summary,
            text_content=text_content,
            text_content_hash=text_content_hash,
            parsed_at=parsed_at
        )

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        try:
            # page title
            title_tag = soup.find(self.selectors.title)
            if title_tag:
                title = title_tag.get_text(strip=True)
                self.logger.info('Title Extracted: %s', title)
                return title
            self.logger.warning('Missing Page Title')
            return None
        except Exception as e:
            self.logger.error(
                f"An exception of type '{type(e).__name__}' occurred: {e}")
            return None

    def _extract_main_body_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        try:
            # content_container_id
            return soup.select_one(self.selectors.content_container_id)
        except Exception as e:
            self.logger.error(
                f"An exception of type '{type(e).__name__}' occurred: {e}")
            return None

    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        try:
            categories = []
            # normal_catlinks_div = soup.find('div', id='mw-normal-catlinks')
            normal_catlinks_div = soup.select_one(
                self.selectors.categories_div_id)
            if normal_catlinks_div:
                category_links = normal_catlinks_div.find_all(
                    self.selectors.links
                )
                for link in category_links:
                    category_text = link.get_text(strip=True)
                    if category_text == 'Categories':
                        continue
                    if category_text.startswith("Category:"):
                        categories.append(category_text[len("Category:"):])
                    else:
                        categories.append(category_text)
            if categories:
                self.logger.info('Categories Extracted: %s', categories)
            else:
                self.logger.warning('Missing Page Categories')
            return categories
        except Exception as e:
            self.logger.error(
                f"An exception of type '{type(e).__name__}' occurred: {e}")
            return []

    def _extract_summary(self, main_content: Tag) -> Optional[str]:
        try:
            paragraphs = main_content.find_all(
                self.selectors.paragraphs
            )

            for p in paragraphs:
                paragraph_text = p.get_text(separator=" ", strip=True)
                if not paragraph_text:
                    continue

                # Filter out boilerplate
                if any(paragraph_text.startswith(prefix) for prefix in [
                    "Coordinates:", "For other uses, see", "This is a redirect"
                ]):
                    continue

                self.logger.info('Summary Extracted: %s', paragraph_text)
                return paragraph_text

            self.logger.warning('Missing Page Summary')
            return None
        except Exception as e:
            self.logger.error(
                f"An exception of type '{type(e).__name__}' occurred: {e}")
            return None

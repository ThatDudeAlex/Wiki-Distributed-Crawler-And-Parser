import logging
from typing import List, Optional

from lxml import html
from readability import Document
from shared.rabbitmq.schemas.save_to_db import SaveParsedContent
from shared.utils import create_hash, get_timestamp_eastern_time


class PageContentExtractor:
    """
    Extracts structured content from raw HTML of Wikipedia-style pages

    Supports extraction of title, categories, main body text, and a content hash.
    Designed for use in a distributed parsing pipeline.
    """

    def __init__(self, configs, logger: logging.Logger):
        self.configs = configs
        self.logger = logger


    def extract(self, url: str, html_content: str) -> SaveParsedContent:
        """
        Parses HTML content from a Wikipedia-like page and returns structured content including
        title, categories, main body text, and a hash of the text content.
        """
        tree = html.fromstring(html_content)

        title = self._extract_title(tree)

        if not title:
            title = 'Page is missing title'

        categories = self._extract_categories(tree)
        main_content_list = self._extract_main_body_content(tree)

        if not main_content_list:
            self.logger.warning('No main content found — skipping text content extraction')
            return SaveParsedContent(
                source_page_url=url,
                title=title,
                categories=categories,
                parsed_at=get_timestamp_eastern_time(isoformat=True)
            )

        text_content = self._extract_clean_text(html_content)
        text_content_hash = create_hash(text_content) if text_content else None

        return SaveParsedContent(
            source_page_url=url,
            title=title,
            categories=categories,
            text_content=text_content,
            text_content_hash=text_content_hash,
            parsed_at=get_timestamp_eastern_time(isoformat=True)
        )


    def _extract_title(self, tree) -> Optional[str]:
        """
        Extracts the page title using the XPath selector defined in the config.
        Returns None if the title is not found or an error occurs.
        """
        try:
            title_list = tree.xpath(self.configs['selectors']['title'])
            if title_list:
                return title_list[0].strip()

            self.logger.warning('Missing Page Title')
            return None
        
        except Exception:
            self.logger.exception("Unexpected error while extracting page title")
            return None


    def _extract_main_body_content(self, tree) -> Optional[List[html.HtmlElement]]:
        """
        Retrieves the main content container from the HTML tree.
        Returns a list of matching elements, or None on failure.
        """
        try:
            return tree.xpath(self.configs['selectors']['content_container_id'])
        
        except Exception:
            self.logger.exception("Unexpected error while extracting page main body content")
            return None


    def _extract_categories(self, tree) -> List[str]:
        """
        Extracts category names from the page using XPath selectors.
        Skips any links labeled 'Categories' or lacking useful structure.
        """
        try:
            categories = []

            normal_catlinks_div_list = tree.xpath(
                self.configs['selectors']['categories_div_id'])

            if normal_catlinks_div_list:
                catlinks_div = normal_catlinks_div_list[0]
                category_links = catlinks_div.xpath(
                    self.configs['selectors']['categories_links']
                )

                for link in category_links:
                    if link == 'Categories':
                        continue
                    if link.startswith("Category:"):
                        categories.append(link[len("Category:"):])
                    else:
                        categories.append(link)

            return categories
        
        except Exception:
            self.logger.exception("Unexpected error while extracting page categories")
            return []


    def _extract_clean_text(self, html_content: str) -> Optional[str]:
        """
        Uses the Readability algorithm to extract cleaned body text from HTML.
        Returns a newline-separated string or None if extraction fails.
        """
        try:
            doc = Document(html_content)
            clean_html = doc.summary()

            if not clean_html:
                return None
            
            tmp_tree = html.fromstring(clean_html)

            text = tmp_tree.text_content().strip()
            return '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        except Exception as e:
            self.logger.warning("Failed to extract clean text: %s", e)
            return None

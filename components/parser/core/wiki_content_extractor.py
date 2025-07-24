import logging
from typing import List, Optional
from bs4 import Tag
from lxml import html
from readability import Document
from shared.rabbitmq.schemas.save_to_db import SaveParsedContent
from shared.utils import create_hash, get_timestamp_eastern_time


class PageContentExtractor:
    def __init__(self, configs, logger: logging.Logger):
        self.configs = configs
        self.logger = logger

    def extract(self, url: str, html_content: str) -> SaveParsedContent:
        """
        Parses HTML content from a Wikipedia-like page and returns structured content including
        title, categories, summary, main body text, and a hash of the text content.
        """
        tree = html.fromstring(html_content)

        title = self._extract_title(tree)
        categories = self._extract_categories(tree)
        main_content_list = self._extract_main_body_content(tree)

        text_content = None
        text_content_hash = None

        if main_content_list:
            doc = Document(html_content)
            clean_html = doc.summary()
            tmp_tree = html.fromstring(clean_html)

            text_content = tmp_tree.text_content().strip()
            text_content = '\n'.join(line.strip() for line in text_content.splitlines() if line.strip())
            text_content_hash = create_hash(text_content)
        else:
            self.logger.warning(
                'Failed to find main content — skipping text_content')

        parsed_at = get_timestamp_eastern_time(isoformat=True)
        return SaveParsedContent(
            source_page_url=url,
            title=title,
            categories=categories,
            text_content=text_content,
            text_content_hash=text_content_hash,
            parsed_at=parsed_at
        )

    def _extract_title(self, tree) -> Optional[str]:
        try:
            title_list = tree.xpath(self.configs['selectors']['title'])
            if title_list:
                return title_list[0].strip()

            self.logger.warning('Missing Page Title')
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error while extracting page title: %s", e)
            return None

    def _extract_main_body_content(self, tree) -> Optional[Tag]:
        try:
            # content_container_id
            return tree.xpath(self.configs['selectors']['content_container_id'])
        except Exception as e:
            self.logger.error(
                f"An exception of type '{type(e).__name__}' occurred: {e}")
            return None

    def _extract_categories(self, tree) -> List[str]:
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
            # if categories:
            #     self.logger.info('Categories Extracted: %s', categories)
            # else:
            #     self.logger.warning('Missing Page Categories')
            return categories
        except Exception as e:
            self.logger.error("Unexpected error extracting categories: %s", e)
            return []

import logging
from urllib.parse import urlparse
from typing import List

from bs4 import BeautifulSoup, Tag
from components.parser.configs.app_configs import WIKIPEDIA_MAIN_BODY_ID, IMAGE_EXTENSIONS
from components.parser.configs.types import LinkData
from shared.utils import is_external_link, normalize_url


class _WikipediaLinkExtractor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def extract(self, page_url: str, html_content: str, depth: int) -> LinkData:
        """
        Parses a Wikipedia HTML page and returns structured data for links within the main body
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            self.logger.error(
                f"Failed to parse HTML for {page_url}: {e}", exc_info=True)
            return []

        main = soup.find('div', id=WIKIPEDIA_MAIN_BODY_ID)
        if main is None:
            self.logger.warning(
                f"No main body ('{WIKIPEDIA_MAIN_BODY_ID}') on {page_url}")
            return []

        results: List[LinkData] = []
        for a in main.find_all('a'):
            data = self._extract_link(a, page_url, depth)
            if data is not None:
                results.append(data)

        if not results:
            self.logger.info(f"No links found in main body of {page_url}")

        return results

    def _extract_link(self, tag: Tag, page_url: str, depth: str) -> LinkData:
        """
        Extracts metadata from an <a> tag and returns structured LinkData
        """
        href = tag.get('href')
        if not href:
            return None

        try:
            normalized_href = normalize_url(href)
            is_internal = not is_external_link(normalized_href)
            text_content = tag.get_text(strip=True)
            title_attribute = tag.get('title')
            id_attribute = tag.get('id')

            rel_list = tag.get('rel')
            rel_attribute = None if not rel_list else " ".join(rel_list)

            link_type = self._determine_type(
                is_internal, normalized_href, href, rel_attribute, text_content
            )

            return LinkData(
                url=normalized_href,
                depth=depth + 1,  # update the depth of the link
                anchor_text=text_content,
                title_attribute=title_attribute,
                rel_attribute=rel_attribute,
                id_attribute=id_attribute,
                link_type=link_type,
                is_internal=is_internal
            )
        except Exception as e:
            self.logger.error(
                f"Error extracting link '{href}' on page '{page_url}': {e}", exc_info=True
            )
            return None

    def _determine_type(
        self,
        is_internal: bool,
        norm_url: str,
        raw_href: str,
        rel: str,
        text: str
    ) -> str:
        """
        Classifies a URL based on its structure, domain, and metadata
        """
        try:
            if is_internal:
                path = urlparse(norm_url).path
                if path.startswith('/wiki/Category:'):
                    return 'category_link'
                if path.startswith('/wiki/File:'):
                    return 'file_link'
                if path.startswith('/wiki/') and not path.lower().endswith(IMAGE_EXTENSIONS):
                    return 'wikilink'
                return 'internal_other'
            else:
                if raw_href.lower().endswith(IMAGE_EXTENSIONS) or text.lower().endswith(IMAGE_EXTENSIONS):
                    return 'external_image_link'
                if rel and 'nofollow' == rel:
                    return 'external_link_nofollow'
                return 'external_link'
        except Exception as e:
            self.logger.error(
                f"Error determining link type for '{raw_href}': {e}", exc_info=True)
            return 'error_determining_type'


def extract_wiki_page_links(page_url: str, html_content: str, depth: int, logger: logging.Logger) -> List[LinkData]:
    """
    Extracts and classifies anchor links from the main body of a Wikipedia page
    """
    extractor = _WikipediaLinkExtractor(logger)
    return extractor.extract(page_url, html_content, depth)

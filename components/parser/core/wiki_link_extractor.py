import logging
from urllib.parse import urlparse
from typing import List

from bs4 import BeautifulSoup, Tag
from components.parser.configs.app_configs import WIKIPEDIA_MAIN_BODY_ID, IMAGE_EXTENSIONS
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData
from shared.utils import get_timestamp_eastern_time
from shared.utils import is_internal_link, normalize_url


class PageLinkExtractor:
    def __init__(self, selectors, logger: logging.Logger):
        self.selectors = selectors
        self.logger = logger

    def extract(self, source_page_url: str, html_content: str, depth: int) -> LinkData:
        """
        Parses a Wikipedia HTML page and returns structured data for links within the main body
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            self.logger.error(
                f"Failed to parse HTML for {source_page_url}: {e}", exc_info=True)
            return []

        main = soup.select_one(self.selectors.content_container_id)
        if main is None:
            self.logger.warning(
                f"No main body ('{self.selectors.content_container_id}') on {source_page_url}")
            return []

        results: List[LinkData] = []
        for a in main.find_all(self.selectors.links):
            data = self._extract_link(a, source_page_url, depth)
            if data is not None:
                results.append(data)

        if not results:
            self.logger.info(
                f"No links found in main body of {source_page_url}")

        return results

    def _extract_link(self, link_tag: Tag, source_page_url: str, depth: str) -> LinkData:
        """
        Extracts metadata from an <a> tag and returns structured LinkData
        """
        href = link_tag.get('href')
        if not href:
            return None

        try:
            normalized_href = normalize_url(href)
            is_internal = is_internal_link(normalized_href)
            text_content = link_tag.get_text(strip=True)

            # Dynamically extract attributes
            link_attributes = {
                attr: link_tag.get(attr) for attr in self.selectors.attributes
            }

            if link_attributes['rel']:
                link_attributes['rel'] = " ".join(link_attributes['rel'])

            link_type = self._determine_type(
                is_internal, normalized_href, href, text_content, link_attributes['rel']
            )

            return LinkData(
                source_page_url=source_page_url,
                url=normalized_href,
                depth=depth + 1,  # update the depth of the link
                discovered_at=get_timestamp_eastern_time(True),
                anchor_text=text_content,
                title_attribute=link_attributes['title'],
                rel_attribute=link_attributes['rel'],
                id_attribute=link_attributes['id'],
                link_type=link_type,
                is_internal=is_internal
            )
        except Exception as e:
            self.logger.error(
                f"Error extracting link '{href}' on page '{source_page_url}': {e}", exc_info=True
            )
            return None

    def _determine_type(
        self,
        is_internal: bool,
        norm_url: str,
        raw_href: str,
        text: str,
        rel: str
    ) -> str:
        """
        Classifies a URL based on its structure, domain, and metadata
        """
        # TODO: Organize these link types the yml configs
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

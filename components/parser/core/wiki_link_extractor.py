import logging
from urllib.parse import urlparse
from typing import List
from lxml import html
from components.parser.configs.app_configs import IMAGE_EXTENSIONS
from shared.rabbitmq.schemas.scheduling import LinkData
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
        tree = html.fromstring(html_content)
        main_list = tree.xpath(self.selectors.content_container_id)

        if not main_list:
            self.logger.warning(
                "No main body while extracting links: %s", source_page_url)
            return []

        main_content = main_list[0]
        all_links = main_content.xpath(self.selectors.all_links)
        extracted_links: List[LinkData] = []

        for link in all_links:
            data = self._construct_link_data(link, source_page_url, depth)

            if data:
                extracted_links.append(data)

        if not extracted_links:
            self.logger.warning(
                "No links found in main body of %s", source_page_url)

        return extracted_links

    def _construct_link_data(self, link, source_page_url: str, depth: str):
        href = link.get('href') or ''

        if not href:
            return None

        anchor_text = link.text_content().strip()
        normalized_href = normalize_url(href)
        is_internal = is_internal_link(normalized_href)

        title_attr = link.get('title') or ''
        rel_attr = link.get('rel') or ''
        id_attr = link.get('id') or ''
        type = self._determine_type(
            is_internal, normalized_href, href, anchor_text, rel_attr
        )
        return LinkData(
            source_page_url=source_page_url,
            url=normalized_href,
            depth=depth + 1,  # update the depth of the link
            discovered_at=get_timestamp_eastern_time(isoformat=True),
            anchor_text=anchor_text,
            title_attribute=title_attr,
            rel_attribute=rel_attr,
            id_attribute=id_attr,
            link_type=type,
            is_internal=is_internal
        )

    def _extract_link(self, link_tag, source_page_url: str, depth: str) -> LinkData:
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
            self.logger.error("Unexpected error extracting data: %s", e)
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
        try:
            rel = (rel or "").lower()
            text = (text or "").lower()
            raw_href = (raw_href or "").lower()
            path = urlparse(norm_url).path.lower()

            if is_internal:
                if path.startswith('/wiki/category:'):
                    return 'category_link'
                if path.startswith('/wiki/file:'):
                    return 'file_link'
                if path.startswith('/wiki/') and not path.endswith(IMAGE_EXTENSIONS):
                    return 'wikilink'
                return 'internal_other'

            # External link classification
            if raw_href.endswith(IMAGE_EXTENSIONS) or text.endswith(IMAGE_EXTENSIONS):
                return 'external_image_link'
            if 'nofollow' in rel:
                return 'external_link_nofollow'
            return 'external_link'

        except Exception as e:
            self.logger.error(
                f"Error determining link type for '{raw_href}': {e}", exc_info=True)
            return 'error_determining_type'

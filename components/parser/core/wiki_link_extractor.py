import logging
from typing import List, Optional
from urllib.parse import urljoin, urlparse, urlunparse

from lxml import html
from shared.rabbitmq.schemas.scheduling import LinkData
from shared.utils import get_timestamp_eastern_time


class PageLinkExtractor:
    """
    Extracts and classifies hyperlinks from the main content section of a Wikipedia-style HTML page
    """

    def __init__(self, configs, logger: logging.Logger):
        """
        Initializes the PageLinkExtractor

        Args:
            configs (dict): Configuration dictionary containing XPath selectors and image extensions
            logger (logging.Logger): Logger instance
        """
        self.configs = configs
        self.logger = logger
        self.image_extensions = tuple(self.configs['selectors']['image_extensions'])


    def extract(self, source_page_url: str, html_content: str, depth: int) -> List[LinkData]:
        """
        Extracts and classifies hyperlinks from the main content of a Wikipedia-style HTML page

        Args:
            source_page_url (str): The original page URL being parsed
            html_content (str): Raw HTML content of the page
            depth (int): The crawl depth of the current page

        Returns:
            List[LinkData]: A list of structured LinkData objects
        """
        tree = html.fromstring(html_content)
        main_list = tree.xpath(self.configs['selectors']['content_container_id'])

        if not main_list:
            self.logger.warning("No main content found: %s", source_page_url)
            return []

        main_content = main_list[0]
        raw_links = main_content.xpath(self.configs['selectors']['all_links'])
        extracted_links: List[LinkData] = []

        for link in raw_links:
            link_data = self._build_link_data(link, source_page_url, depth)
            if link_data:
                extracted_links.append(link_data)

        if not extracted_links:
            self.logger.warning("No valid links found: %s", source_page_url)

        return extracted_links


    def _build_link_data(self, link, source_page_url: str, depth: int) -> Optional[LinkData]:
        """
        Constructs a LinkData object from a single <a> element

        Args:
            link: lxml Element representing the <a> tag
            source_page_url (str): URL of the page containing the link
            depth (int): Current depth of crawling

        Returns:
            Optional[LinkData]: Structured link object, or None if invalid or error occurs
        """
        href = link.get('href')
        if not href:
            return None

        try:
            normalized_href = self.normalize_url(href)
            is_internal = self.is_internal_link(normalized_href)

            # extract link attributes
            anchor_text = (link.text_content() or '').strip()
            rel_attr = link.get('rel') or ''
            title_attr = link.get('title') or ''
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
        
        except Exception:
            self.logger.exception("Error extracting link data")
            return None
        
    
    def normalize_url(self, href: str) -> str:
        """
        Normalizes a URL by converting to absolute, and removing fragments/query parameters.
        """
        # Convert relative URL to absolute
        full_url = urljoin(self.configs['wikipedia']['base_url'], href)

        # Remove fragments (#section) and query params (?foo=bar)
        parsed = urlparse(full_url)
        cleaned = parsed._replace(fragment="", query="")
        return urlunparse(cleaned)
    
    
    def is_internal_link(self, href: str) -> bool:
        """
        Determines if a given href points to an internal (Wikipedia) link
        """
        parsed = urlparse(href)
        # Check for http/https scheme and ensure it's in a Wikipedia domain
        # 'wikipedia.org'
        return (
            parsed.scheme in ["http", "https"]
            and self.configs['wikipedia']['domain'] in parsed.netloc
        )


    def _determine_type(
        self,
        is_internal: bool,
        norm_url: str,
        raw_href: str,
        text: str,
        rel: str
    ) -> str:
        """
        Determines the classification of a link based on its structure and metadata

        Args:
            is_internal (bool): Whether the link is internal to the target domain
            norm_url (str): Normalized URL of the link
            raw_href (str): Raw href string
            text (str): Anchor text of the link
            rel (str): Value of the 'rel' attribute

        Returns:
            str: The classification the input link falls under
        """
        try:
            path = urlparse(norm_url).path.lower()
            raw_href = raw_href.lower()
            text = text.lower()
            rel = rel.lower()

            if is_internal:
                if path.startswith('/wiki/category:'):
                    return 'category_link'
                if path.startswith('/wiki/file:'):
                    return 'file_link'
                if path.startswith('/wiki/') and not path.endswith(self.image_extensions):
                    return 'wikilink'
                return 'internal_other'

            # External link classification
            if raw_href.endswith(self.image_extensions) or text.endswith(self.image_extensions):
                return 'external_image_link'
            if 'nofollow' in rel:
                return 'external_link_nofollow'
            return 'external_link'

        except Exception:
            self.logger.exception(f"Error classifying link: {raw_href}")
            return 'error_determining_type'

"""
Filtering service for validating whether a discovered link should be scheduled for crawling

Includes logic for:
    - Maximum depth enforcement
    - Domain and language filtering
    - Excluded prefixes
    - Home page filtering
    - robots.txt disallow rules
"""

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from shared.rabbitmq.schemas.scheduling import LinkData
from shared.utils import is_external_link, has_excluded_prefix, is_home_page


class FilteringService:
    def __init__(self, configs, logger: logging.Logger):
        self.configs = configs
        self._logger = logger
        self.robots_parser = self._load_robots_txt(
            configs['filters']['robots_txt']
        )

    def _load_robots_txt(self, robots_url) -> RobotFileParser:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except Exception:
            self._logger.warning("Failed to read robots.txt from: %s", robots_url)
        return parser

    def is_filtered(self, link: LinkData) -> bool:
        """
        Determines whether a given link should be excluded from crawling
        based on filtering rules

        Returns:
            True if the link should be filtered, else False
        """
        return (
            self._exceeds_max_depth(link) or
            self._is_external(link) or
            self._is_not_article_page(link) or
            self._is_cross_language_domain(link) or
            self._is_blocked_by_robot(link)
        )

    def _exceeds_max_depth(self, link: LinkData) -> bool:
        return link.depth > self.configs['filters']['max_depth']

    def _is_external(self, link: LinkData) -> bool:
        return is_external_link(link.url)

    def _is_not_article_page(self, link: LinkData) -> bool:
        return has_excluded_prefix(link.url) or is_home_page(link.url)

    def _is_cross_language_domain(self, link: LinkData) -> bool:
        parsed = urlparse(link.url)
        return parsed.netloc not in self.configs['filters']['allowed_domains']

    def _is_blocked_by_robot(self, link: LinkData) -> bool:
        path = urlparse(link.url).path
        return not self.robots_parser.can_fetch(
            self.configs['http_headers']['user-agent'], path
        )

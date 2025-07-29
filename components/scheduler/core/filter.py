import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from components.scheduler.monitoring.metrics import FILTERED_LINKS_TOTAL
from shared.rabbitmq.schemas.scheduling import LinkData


class FilteringService:
    """
    Provides filtering logic to determine whether a discovered link should be excluded
    from the crawling pipeline.

    Filters include:
        - Max crawl depth
        - Domain restrictions
        - Prefix/path exclusions
        - robots.txt disallow rules
        - Home page exclusion

    Attributes:
        _configs (dict): Component-specific filtering configuration.
        _logger (logging.Logger): Logger for diagnostics.
        _robots_parser (RobotFileParser): Preloaded robots.txt parser.
    """

    def __init__(self, configs, logger: logging.Logger):
        self._configs = configs
        self._logger = logger
        self._robots_parser = self._load_robots_txt(
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
            True if the link should be filtered, False otherwise
        """
        return (
            self._exceeds_max_depth(link) or
            self._is_external_domain(link) or
            self._is_not_article_page(link) or
            self._is_blocked_by_robot(link)
        )

    def _exceeds_max_depth(self, link: LinkData) -> bool:
        if link.depth > self._configs['filters']['max_depth']:
            FILTERED_LINKS_TOTAL.labels(filter_type="depth").inc()
            return True
        return False


    def _is_external_domain(self, link: LinkData) -> bool:
        parsed = urlparse(link.url)
        if parsed.netloc not in self._configs['filters']['allowed_domains']:
            FILTERED_LINKS_TOTAL.labels(filter_type="domain").inc()
            return True
        return False


    def _is_not_article_page(self, link: LinkData) -> bool:
        return self._has_excluded_prefix(link.url) or self._is_home_page(link.url)


    def _is_blocked_by_robot(self, link: LinkData) -> bool:
        path = urlparse(link.url).path
        allowed = self._robots_parser.can_fetch(
            self._configs['http_headers']['user-agent'], path
        )

        if not allowed:
            FILTERED_LINKS_TOTAL.labels(filter_type="robots_txt").inc()

        return not allowed
    

    def _has_excluded_prefix(self, url: str) -> bool:
        # strip fragment/query to test path alone
        path = urlparse(url).path
        excluded_prefixes = self._configs.get("filters", {}).get("excluded_prefixes", [])

        # check if it's in any excluded namespace
        for prefix in excluded_prefixes:
            if path.startswith(prefix):
                FILTERED_LINKS_TOTAL.labels(filter_type="prefix").inc()
                return True
        return False
    
    
    def _is_home_page(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.path.strip("/") == "" and parsed.netloc in ["", "en.wikipedia.org"]:
            FILTERED_LINKS_TOTAL.labels(filter_type="home_page").inc()
            return True
        return False
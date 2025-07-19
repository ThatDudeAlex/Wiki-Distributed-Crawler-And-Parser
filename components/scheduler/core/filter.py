from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from shared.rabbitmq.schemas.scheduling import LinkData
from shared.config import BASE_HEADERS
from shared.utils import is_external_link, has_excluded_prefix, is_home_page
import logging

# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed

# TODO: Implement global config loading for base headers


class FilteringService:
    def __init__(self, configs, logger: logging.Logger):
        self.configs = configs
        self._logger = logger
        self.robots_parser = self._load_robots_txt(
            configs.filters.robots_txt
        )

    def _load_robots_txt(self, robot_text) -> RobotFileParser:
        robots_url = robot_text
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.read()
        return parser

    def is_filtered(self, link: LinkData) -> bool:
        return (
            self._exceeds_max_depth(link) or
            self._is_external(link) or
            self._is_not_article_page(link) or
            self._is_cross_language_domain(link) or
            self._is_blocked_by_robot(link)
        )

    def _exceeds_max_depth(self, link: LinkData) -> bool:
        if link.depth > self.configs.filters.max_depth:
            # self._logger.info(
            #     "FILTERED: Exceeds max depth — depth=%s > MAX_DEPTH=%s — URL: %s",
            #     link.depth, self.configs.filters.max_depth, link.url
            # )
            return True
        return False

    def _is_external(self, link: LinkData) -> bool:
        if is_external_link(link.url):
            # self._logger.info("FILTERED: External link — URL: %s", link.url)
            return True
        return False

    def _is_not_article_page(self, link: LinkData) -> bool:
        if has_excluded_prefix(link.url):
            # self._logger.info("FILTERED: Excluded prefix — URL: %s", link.url)
            return True

        if is_home_page(link.url):
            # self._logger.info("FILTERED: Home page — URL: %s", link.url)
            return True

        return False

    def _is_cross_language_domain(self, link: LinkData) -> bool:
        parsed = urlparse(link.url)
        if parsed.netloc not in self.configs.filters.allowed_domains:
            # self._logger.info("FILTERED: Unallowed Domain — URL: %s", link.url)
            return True
        return False

    def _is_blocked_by_robot(self, link: LinkData) -> bool:
        path = urlparse(link.url).path
        is_allowed = self.robots_parser.can_fetch(
            BASE_HEADERS['user-agent'], path)

        if is_allowed:
            return False

        # self._logger.info(
        #     "FILTERED: Blocked by robots.txt — URL: %s", link.url)
        return True

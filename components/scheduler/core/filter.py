import logging
from urllib.parse import urlparse
from shared.rabbitmq.types import DiscoveredLink
from shared.config import MAX_DEPTH
from shared.utils import is_external_link, has_excluded_prefix, is_home_page
from components.scheduler.services.robot_checker import robot_blocks_crawling


def is_filtered(link: DiscoveredLink) -> bool:
    if (
            exceeds_max_depth(link) or is_external(link) or
            is_not_article_page(link) or is_blocked_by_robot(link)
    ):
        return True

    return False


def exceeds_max_depth(link: DiscoveredLink) -> bool:
    if link.depth > MAX_DEPTH:
        return True


def is_external(link: DiscoveredLink) -> bool:
    return is_external_link(link.url)


def is_not_article_page(link: DiscoveredLink) -> bool:
    return has_excluded_prefix(link.url) or is_home_page(link.url)


def is_blocked_by_robot(link: DiscoveredLink) -> bool:
    return robot_blocks_crawling(link.url)

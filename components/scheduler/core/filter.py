import logging
from urllib.parse import urlparse
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData
from shared.config import MAX_DEPTH
from shared.utils import is_external_link, has_excluded_prefix, is_home_page
from components.scheduler.services.robot_checker import robot_blocks_crawling


def is_filtered(link: LinkData) -> bool:
    if (
            exceeds_max_depth(link) or is_external(link) or
            is_not_article_page(link) or is_blocked_by_robot(link)
    ):
        return True

    return False


def exceeds_max_depth(link: LinkData) -> bool:
    if link.depth > MAX_DEPTH:
        return True


def is_external(link: LinkData) -> bool:
    return is_external_link(link.url)


def is_not_article_page(link: LinkData) -> bool:
    return has_excluded_prefix(link.url) or is_home_page(link.url)


def is_blocked_by_robot(link: LinkData) -> bool:
    return robot_blocks_crawling(link.url)

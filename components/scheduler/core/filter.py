from urllib.parse import urlparse
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData
from shared.config import MAX_DEPTH
from shared.utils import is_external_link, has_excluded_prefix, is_home_page
from components.scheduler.services.robot_checker import robot_blocks_crawling
import logging


def is_filtered(link: LinkData, logger: logging.Logger) -> bool:
    return (
        exceeds_max_depth(link, logger)
        or is_external(link, logger)
        or is_not_article_page(link, logger)
        or is_blocked_by_robot(link, logger)
    )


def exceeds_max_depth(link: LinkData, logger: logging.Logger) -> bool:
    if link.depth > MAX_DEPTH:
        logger.info(
            "FILTERED: Exceeds max depth — depth=%s > MAX_DEPTH=%s — URL: %s",
            link.depth, MAX_DEPTH, link.url
        )
        return True
    return False


def is_external(link: LinkData, logger: logging.Logger) -> bool:
    if is_external_link(link.url):
        logger.info("FILTERED: External link — URL: %s", link.url)
        return True
    return False


def is_not_article_page(link: LinkData, logger: logging.Logger) -> bool:
    if has_excluded_prefix(link.url):
        logger.info("FILTERED: Excluded prefix — URL: %s", link.url)
        return True
    if is_home_page(link.url):
        logger.info("FILTERED: Home page — URL: %s", link.url)
        return True
    return False


def is_blocked_by_robot(link: LinkData, logger: logging.Logger) -> bool:
    if robot_blocks_crawling(link.url):
        logger.info("FILTERED: Blocked by robots.txt — URL: %s", link.url)
        return True
    return False

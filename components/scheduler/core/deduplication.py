
import logging
import requests
from urllib.parse import urljoin
from shared.redis.cache_service import CacheService


def has_duplicates(url: str, dbhost: str, cache: CacheService, logger: logging.Logger) -> bool:
    if cache.is_seen_url(url):
        return True

    logger.info('Checking DB Reader API for URL: %s', url)
    db_seen = _in_db_cache(url, dbhost)

    if db_seen is True:
        logger.debug("URL '%s' found in DB Reader API.", url)
        # If found in DB but not Redis, add to Redis to speed up future checks
        cache.add_to_seen_set(url)
        logger.debug(
            "URL '%s' added to Redis cache from DB lookup.", url)
        return True

    logger.debug("URL '%s' not found in DB Reader API.", url)
    return False


def _in_db_cache(url: str, dbhost: str) -> bool:
    db_url = urljoin(dbhost, '/url_cache')
    response = requests.get(db_url, params={"url": url}, timeout=5.0)
    data = response.json()

    if data['is_cached']:
        return True
    return False

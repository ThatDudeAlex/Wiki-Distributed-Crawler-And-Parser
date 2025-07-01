import logging
import redis
from shared.redis.cache_config import CacheSets


class CacheService:
    def __init__(self, logger: logging.Logger):
        if not logger:
            raise ValueError("logger is required")

        self._redis = redis.Redis(
            host='redis', port=6379, decode_responses=True)
        self._logger = logger

    def add_to_enqueued_set(self, url: str) -> bool:
        """
        Add ``URL`` to the ``enqueued`` set

        Returns ``True`` if it successfully adds the ``URL`` else returns ``False``
        """
        if url:
            self._redis.sadd(CacheSets.SEEN.value, url)
            self._logger.info(f"Added to enqueued set: {url}")
            return True
        return False

    def add_to_visited_set(self, url: str) -> bool:
        """
        Add ``URL`` to the ``visited`` set

        Returns ``True`` if it successfully adds the ``URL`` else returns ``False``
        """
        if url:
            self._redis.sadd(CacheSets.VISITED.value, url)
            self._logger.info(f"Added to visited set: {url}")
            return True
        return False

    def set_if_not_existing(self, url: str) -> bool:
        """
        Sets the ``key`` if it doesn't exist. 
        returns ``True`` only if the key is set, else
        returns ``False``
        """
        is_seeded = self._redis.set(f"enqueued:{url}", 1, nx=True)
        if is_seeded:
            self._logger.info(f"Set initiating seed key for: {url}")
        return is_seeded

    def is_in_visited(self, url: str) -> bool:
        return self._redis.sismember(CacheSets.VISITED.value, url)

    def is_in_enqueued(self, url: str) -> bool:
        return self._redis.sismember(CacheSets.SEEN.value, url)

    def is_queueable(self, url: str) -> bool:
        return not self.is_in_visited(url) and not self.is_in_enqueued(url)

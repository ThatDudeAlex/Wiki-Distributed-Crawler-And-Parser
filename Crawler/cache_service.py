import redis
from shared.config import R_VISITED, R_ENQUEUED


class CacheService:
    def __init__(self, logger):
        self._redis = redis.Redis(
            host='redis', port=6379, decode_responses=True)
        self._logger = logger

    def add_to_enqueued_set(self, url: str) -> bool:
        """
        Add ``URL`` to the ``enqueued`` set
        and returns true
        """
        self._redis.sadd(R_ENQUEUED, url)
        self._logger.info(f"Added to enqueued set: {url}")
        return True

    def add_to_visited_set(self, url: str) -> bool:
        """
        Add ``URL`` to the ``visited`` set
        and returns true
        """
        self._redis.sadd(R_VISITED, url)
        self._logger.info(f"Added to visited set: {url}")
        return True

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

    def is_queueable(self, url):
        in_visited = self._redis.sismember(R_VISITED, url)
        in_enqueued = self._redis.sismember(R_ENQUEUED, url)

        if in_visited or in_enqueued:
            return False
        return True

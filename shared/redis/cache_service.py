import logging
import time
import redis
import redis.exceptions

# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed


class CacheService:
    def __init__(self, logger: logging.Logger):
        if not logger:
            raise ValueError("logger is required")

        self._redis = redis.Redis(
            host='redis', port=6379, decode_responses=True)
        # self._expiration_seconds = 3600  # 1hr
        self._logger = logger

    def batch_is_seen_url(self, urls: list[str]) -> list[bool]:
        """
        Checks if each of the URLs in the input list exist, are cached

        Returns ``list[bool]`` to represent if a URL exist in the cache or not
        """
        results = []
        try:
            with self._redis.pipeline() as pipe:
                for url in urls:
                    pipe.exists(url)
                results = pipe.execute()

            # Convert 1s and 0s to True/False with list comprehension
            return [bool(r) for r in results]
        except redis.exceptions.RedisError as e:
            self._logger.warning(
                'Redis batch check failed: %s', e, exc_info=True)
            # Fail-safe: treat all as unseen
            return [False] * len(urls)

    def add_to_seen_set(self, url: str) -> bool:
        """
        Add ``URL`` to the ``seen`` set

        Returns ``True`` if it successfully adds the ``URL`` else returns ``False``
        """
        try:
            if url:
                # cache url temporarily
                was_added = self._redis.set(url, 1, nx=True)
                return was_added is True
            return False
        except redis.exceptions.RedisError as e:
            self._logger.warning(
                'Redis insert failed: %s (URL: %s)', e, url, exc_info=True)
            return False

    def is_seen_url(self, url: str) -> bool:
        try:
            if not url:
                # self._logger.warning(
                #     'No URL provided.. Skipping Redis Cache Check')
                return False

            if self._redis.exists(url):
                # self._logger.info('URL found in Redis: %s', url)
                return True
            else:
                # self._logger.info(
                #     'URL not found in Redis, checking DB cache for: %s', url)
                return False
        except redis.exceptions.RedisError as e:
            self._logger.warning(
                'Redis Cache check failed: %s (URL: %s)', e, url, exc_info=True)
            return False

    def submit_heartbeat(self, key: str, ttl: int):
        self._redis.set(key, time.time(), ex=ttl)

    def get_heartbeat_count(self, key_pattern, scan_count):
        count = 0
        cursor = 0

        while True:
            cursor, keys = self._redis.scan(
                cursor=cursor, match=key_pattern, count=scan_count)
            count += len(keys)
            if cursor == 0:
                break

        return count

    # TODO: Used for testing, remove or make private
    def inspect_submitted_heartbeat(self, key: str):
        value = self._redis.get(key)
        ttl = self._redis.ttl(key)

        if value is not None:
            # since it's stored as time.time(), cast it back to float
            value = float(value)
        return {
            "key": key,
            "value": value,
            "ttl": ttl
        }

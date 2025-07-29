import logging
from typing import Any
import redis
import redis.exceptions

# TODO: I temporarily commented out logging to test how it affects performace
#       put them back when needed


class CacheService:
    """
    Service class for managing a Redis-backed cache of seen URLs.

    This class provides methods to:
        - Add URLs to the "seen" set
        - Check if individual or batch URLs have been seen before
        - Integrate with Redis for fast, in-memory deduplication

    Attributes:
        _redis (redis.Redis): Redis client instance for caching operations.
        _logger (logging.Logger): Logger for structured error and debug logging.

    Args:
        redis_configs (dict[str, Any]): Configuration dictionary with Redis connection settings.
            Required keys:
                - 'host' (str): Redis host address.
                - 'port' (int): Redis port number.
            Optional keys:
                - 'decode_responses' (bool): Whether to decode byte responses to strings. Defaults to True.

        logger (logging.Logger): Logger instance.

    Raises:
        ValueError: If required Redis config keys are missing or logger is not provided.
    """

    def __init__(self, redis_configs: dict[str, Any], logger: logging.Logger):
        if not logger:
            raise ValueError("logger is required")
        
        required_keys = ['host', 'port']
        for key in required_keys:
            if key not in redis_configs:
                raise ValueError(f"Missing required Redis config key: {key}")

        self._redis = redis.Redis(
            host=redis_configs['host'], 
            port=redis_configs['port'], 
            decode_responses=redis_configs.get('decode_responses', True), 
        )
        self._logger = logger

    def batch_is_seen_url(self, urls: list[str]) -> list[bool]:
        """
        Batch checks if each URL is present in the Redis cache.

        Returns:
            list[bool]: True if URL exists in Redis, False otherwise.
                        On Redis error, returns all False as fail-safe.
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
        Adds the URL to the seen set using SET NX.
        
        Returns:
            True if the URL was newly added to the Redis cache,
            False if it was already seen or insertion failed.
        """
        try:
            if not url:
                return False
            
            was_added = self._redis.set(url, 1, nx=True)
            return bool(was_added)
        
        except redis.exceptions.RedisError as e:
            self._logger.warning(
                'Redis insert failed: %s (URL: %s)', e, url, exc_info=True
            )
            return False


    def is_seen_url(self, url: str) -> bool:
        """
        Checks if a single URL has already been seen.

        Returns:
            True if the URL exists in Redis cache, False otherwise.
        """
        if not url:
            self._logger.warning("No URL provided to is_seen_url — skipping check")
            return False
        
        try:
            return bool(self._redis.exists(url))
        
        except redis.exceptions.RedisError as e:
            self._logger.warning(
                'Redis Cache check failed: %s (URL: %s)', e, url, exc_info=True)
            return False



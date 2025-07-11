import logging
import socket
from shared.redis.cache_service import CacheService


class HeartBeat:
    def __init__(self, configs, logger: logging.Logger):
        self.logger = logger

        # cache setup (for simple heartbeat)
        self.cache = CacheService(logger)

        self.crawler_id = socket.gethostname()
        self.template = configs.heartbeat.key_template
        self.key = self._create_heartbeat_key(self.crawler_id, self.template)
        self.ttl = configs.heartbeat.ttl_seconds
        self._initial_heartbeat(configs.heartbeat.initial_ttl_seconds)
        # self.logger.info("Crawler: %s - Submitted Initial Heartbeat")

    def _create_heartbeat_key(self, crawler_id: str, template: str):
        # Format the key
        return template.format(crawler_id=crawler_id)

    def _initial_heartbeat(self, initial_ttl: int):
        self.cache.submit_heartbeat(self.key, initial_ttl)

    def update_heartbeat(self):
        self.cache.submit_heartbeat(self.key, self.ttl)
        # self.logger.info("Crawler: %s - Updated Heartbeat")

    # TODO: Used for testing, remove or make private
    def inspect_heartbeat(self):
        heartbeat = self.cache.inspect_submitted_heartbeat(self.key)
        # self.logger.info("Heartbeat: %s", heartbeat)

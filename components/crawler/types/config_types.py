from typing import TypedDict


class Logging(TypedDict):
    log_to_file: bool
    log_level: str
    logger_name: str


class Headers(TypedDict):
    accept: str
    accept_language: str
    user_agent: str


class RateLimit(TypedDict):
    max_requests_per_sec: int


class Heartbeat(TypedDict):
    enabled: bool
    interval_seconds: int
    ttl_seconds: int


class CrawlerConfig(TypedDict):
    logging: Logging
    headers: Headers
    rate_limit: RateLimit
    heartbeat: Heartbeat
    storage_path: str

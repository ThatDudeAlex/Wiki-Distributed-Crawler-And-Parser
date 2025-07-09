from typing import TypedDict


class _Logging(TypedDict):
    log_to_file: bool
    log_level: str


class _Headers(TypedDict):
    accept: str
    accept_language: str
    user_agent: str


class _RateLimit(TypedDict):
    max_requests_per_sec: int


class _Heartbeat(TypedDict):
    enabled: bool
    interval_seconds: int
    ttl_seconds: int


class CrawlerConfig(TypedDict):
    logging: _Logging
    headers: _Headers
    rate_limit: _RateLimit
    heartbeat: _Heartbeat
    storage_path: str

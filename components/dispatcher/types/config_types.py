from typing import TypedDict


class Logging(TypedDict):
    log_to_file: bool
    log_level: str
    logger_name: str


class SeedUrls(TypedDict):
    urls: list[str]


class DispatcherConfig(TypedDict):
    logging: Logging
    seed_urls: SeedUrls

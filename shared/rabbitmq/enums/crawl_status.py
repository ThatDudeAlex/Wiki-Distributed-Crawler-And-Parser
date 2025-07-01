from enum import Enum


class CrawlStatus(str, Enum):
    CRAWLED_SUCCESS = "CRAWLED_SUCCESS"
    CRAWL_FAILED = "CRAWL_FAILED"
    SKIPPED = "SKIPPED"

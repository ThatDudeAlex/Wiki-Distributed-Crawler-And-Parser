from enum import Enum


class QueueNames(str, Enum):
    CRAWL = 'crawl_tasks'
    CRAWL_RESULT = 'crawl_result'
    SAVE_PAGE = 'save_crawled_pages'
    PARSE = 'parse_tasks'
    SAVE_CONTENT = 'save_parsed_content'
    PROCESS_LINKS = 'enqueue_links'
    FAILED_TASK = 'save_failed_tasks'

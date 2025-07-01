from enum import Enum

WIKI_BASE = "https://en.wikipedia.org"

SEED_URL = 'https://en.wikipedia.org/wiki/Computer_science'

MAX_DEPTH = 2

ROBOTS_TXT = 'https://en.wikipedia.org/robots.txt'


BASE_HEADERS = {
    'accept': 'text/html',
    'accept-language': 'en-US',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
}

# Excluded Wikimedia namespaces & home page
EXCLUDED_PREFIXES = [
    "/wiki/Special:",
    "/wiki/Help:",
    "/wiki/Portal:",
    "/wiki/File:",
    "/wiki/Template:",
    "/wiki/Template_talk:",
    "/wiki/Wikipedia:",
    "/wiki/Talk:",
    "/wiki/Category:",
    "/wiki/Book:",
    "/wiki/User:",
    "/wiki/Module:",
    "/wiki/Project:",
    "/wiki/Main_Page",
]


class RedisSets(Enum):
    VISITED = 'visited'
    SEEN = 'seen'


class QueueNames(Enum):
    CRAWL = 'crawl_tasks'
    CRAWL_RESULT = 'crawl_result'
    # TODO: move page save to parser instead of crawler
    SAVE_PAGE = 'save_crawled_pages'
    PARSE = 'parse_tasks'
    SAVE_CONTENT = 'save_parsed_content'
    PROCESS_LINKS = 'enqueue_links'
    FAILED_TASK = 'save_failed_tasks'


ALL_QUEUE_CHANNELS = [
    QueueNames.CRAWL.value,
    QueueNames.SAVE_PAGE.value,
    QueueNames.PARSE.value,
    QueueNames.SAVE_CONTENT.value,
    QueueNames.PROCESS_LINKS.value,
    QueueNames.FAILED_TASK.value,
]


CRAWLER_QUEUE_CHANNELS = {
    'listen': QueueNames.CRAWL.value,
    'parsetask': QueueNames.PARSE.value,
    'savepage': QueueNames.SAVE_PAGE.value,
    'failed': QueueNames.FAILED_TASK.value
}


PARSER_QUEUE_CHANNELS = {
    'listen': QueueNames.PARSE.value,
    'savecontent': QueueNames.SAVE_CONTENT.value,
    'enqueuelinks': QueueNames.PROCESS_LINKS.value,
    'failed': QueueNames.FAILED_TASK.value
}


DB_SERVICE_QUEUE_CHANNELS = {
    'savepage': QueueNames.SAVE_PAGE.value,
    'savecontent': QueueNames.SAVE_CONTENT.value,
    'failedtask': QueueNames.FAILED_TASK.value
}

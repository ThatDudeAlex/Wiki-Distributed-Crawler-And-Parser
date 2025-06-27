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

# Wikimedia namespaces & home page
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

# Redis Configs


class RedisSets(Enum):
    VISITED = 'visited'
    ENQUEUED = 'enqueued'


# RabbitMQ Configs
class QueueNames(Enum):
    CRAWL = 'crawl_tasks'
    SAVE_PAGE = 'save_crawled_pages'
    PARSE = 'parse_tasks'
    SAVE_CONTENT = 'save_parsed_content'
    ENQUEUE_LINKS = 'enqueue_links'


CRAWLER_QUEUE_CHANNELS = {
    'listen': QueueNames.CRAWL.value,
    'parsejobs': QueueNames.PARSE.value,
    'savepage': QueueNames.SAVE_PAGE.value,
}

PARSER_QUEUE_CHANNELS = {
    'listen': QueueNames.PARSE.value,
    'savecontent': QueueNames.SAVE_CONTENT.value,
    'enqueuelinks': QueueNames.ENQUEUE_LINKS.value
}

CRAWLER_PUBLISH_SCHEMA = {
    "url": "string",
    "properties": {
        "id": {"type": "integer"},
        "type": {"type": "string"},
        "payload": {"type": "object"}
    },
    "required": ["id", "type", "payload"]
}

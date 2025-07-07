from enum import Enum


class QueueNames(str, Enum):
    """
    Central definition of RabbitMQ queue names used across the system

    These queues support inter-service communication between components like the
    Crawler, Parser, Scheduler, and Storage

    Queues
    ======

    - URLS_TO_CRAWL: Queue of URLs ready to be crawled
    - PAGE_METADATA_TO_SAVE: Extracted metadata from crawled pages to be saved
    - PAGES_TO_PARSE: Fully crawled pages awaiting parsing
    - PARSED_CONTENT_TO_SAVE: Parsed page content ready to be stored
    - LINKS_TO_SCHEDULE: Links extracted from parsed content to be scheduled
    - SCHEDULED_URLS_TO_PROCESS: URLs that have been scheduled and are ready for processing
    - SCHEDULED_LINKS_TO_SAVE: Scheduled links ready to be stored
    - SEEN_LINKS_TO_CACHE: Cache of previously seen links to avoid duplication
    """

    URLS_TO_CRAWL = 'urls_to_crawl'
    PAGE_METADATA_TO_SAVE = 'page_metadata_to_save'
    PAGES_TO_PARSE = 'pages_to_parse'
    PARSED_CONTENT_TO_SAVE = 'parsed_content_to_save'
    LINKS_TO_SCHEDULE = 'links_to_schedule'
    SCHEDULED_LINKS_TO_PROCESS = 'scheduled_urls_to_process'
    SCHEDULED_LINKS_TO_SAVE = 'scheduled_links_to_save'
    SEEN_LINKS_TO_CACHE = 'seen_links_to_cache'
    ADD_LINKS_TO_SCHEDULE = 'add_links_to_schedule'


class EnumCommonMethods:
    """
    Class to provide common methods for Enums
    """
    @classmethod
    def get_values(cls):
        """
        Returns a list of all values defined in the enum
        """
        return [member.value for member in cls]

    @classmethod
    def get_names(cls):
        """
        Returns a list of all names defined in the enum
        """
        return [member.name for member in cls]

    @classmethod
    def get_members(cls):
        """
        Returns a list of all enum members
        """
        return list(cls)


# Crawler queue channels
class CrawlerQueueChannels(EnumCommonMethods, str, Enum):
    """
    Crawler Queue Channels

    Describes which queues are consumed or published by the Crawler

    Consumes
    --------
    - urls_to_crawl

    Publishes
    ---------
    - page_metadata_to_save
    - pages_to_parse
    """
    URLS_TO_CRAWL = QueueNames.URLS_TO_CRAWL.value
    START_TO_CRAWL = 'start_crawl'
    PAGE_METADATA_TO_SAVE = QueueNames.PAGE_METADATA_TO_SAVE.value
    PAGES_TO_PARSE = QueueNames.PAGES_TO_PARSE.value


# Parser queue channels
class ParserQueueChannels(EnumCommonMethods, str, Enum):
    """
    Parser Queue Channels

    Describes which queues are consumed or published by the Parser

    Consumes
    --------
    - pages_to_parse

    Publishes
    ---------
    - parsed_content_to_save
    - links_to_schedule
    """
    PAGES_TO_PARSE = QueueNames.PAGES_TO_PARSE.value
    PARSED_CONTENT_TO_SAVE = QueueNames.PARSED_CONTENT_TO_SAVE.value
    LINKS_TO_SCHEDULE = QueueNames.LINKS_TO_SCHEDULE.value


# DB Writer queue channels
class DbWriterQueueChannels(EnumCommonMethods, str, Enum):
    """
    Db_writer Queue Channels

    Describes which queues are consumed or published by the Db_writer

    Consumes
    --------
    - page_metadata_to_save
    - parsed_content_to_save
    - scheduled_links_to_save
    - seen_links_to_cache
    """
    PAGE_METADATA_TO_SAVE = QueueNames.PAGE_METADATA_TO_SAVE.value
    PARSED_CONTENT_TO_SAVE = QueueNames.PARSED_CONTENT_TO_SAVE.value
    SCHEDULED_LINKS_TO_SAVE = QueueNames.SCHEDULED_LINKS_TO_SAVE.value
    SEEN_LINKS_TO_CACHE = QueueNames.SEEN_LINKS_TO_CACHE.value
    ADD_LINKS_TO_SCHEDULE = QueueNames.ADD_LINKS_TO_SCHEDULE.value


# Scheduler queue channels
class SchedulerQueueChannels(EnumCommonMethods, str, Enum):
    """
    Scheduler Queue Channels

    Describes which queues are consumed or published by the Scheduler

    Consumes
    --------
    - links_to_schedule
    - scheduled_urls_to_process

    Publishes
    ---------
    - leaky_bucket (for rate limiting leaky bucket algorithm)
    - urls_to_crawl
    - scheduled_links_to_save
    - seen_links_to_cache
    """
    LINKS_TO_SCHEDULE = QueueNames.LINKS_TO_SCHEDULE.value
    SCHEDULED_LINKS_TO_PROCESS = QueueNames.SCHEDULED_LINKS_TO_PROCESS.value
    # LEAKY_BUCKET = 'leaky_bucket',
    URLS_TO_CRAWL = QueueNames.URLS_TO_CRAWL.value
    SCHEDULED_LINKS_TO_SAVE = QueueNames.SCHEDULED_LINKS_TO_SAVE.value
    SEEN_LINKS_TO_CACHE = QueueNames.SEEN_LINKS_TO_CACHE.value
    ADD_LINKS_TO_SCHEDULE = QueueNames.ADD_LINKS_TO_SCHEDULE.value

# Scheduler queue channels


class DispatcherQueueChannels(EnumCommonMethods, str, Enum):
    """
    Dispatcher Queue Channels

    Describes which queues are consumed or published by the Dispatcher

    Publishes
    ---------
    - urls_to_crawl
    """
    URLS_TO_CRAWL = QueueNames.URLS_TO_CRAWL.value


class DelayQueues(EnumCommonMethods, str, Enum):
    SCHEDULER_DELAY_30MS = 'scheduler_delay_30ms'
    CRAWLER_DELAY_30MS = 'crawler_delay_30ms'

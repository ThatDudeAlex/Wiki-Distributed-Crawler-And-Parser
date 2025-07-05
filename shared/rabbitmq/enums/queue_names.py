from enum import Enum


class QueueNames(str, Enum):
    # Queues For 'Crawling Task'
    CRAWL_TASK = 'crawl_tasks'
    CRAWL_REPORT = 'crawl_report'
    SAVE_PAGE_DATA = 'save_crawl_data'
    FETCH_PAGE_DATA = 'fetch_page_metadata'

    # Queues For 'Parsing Task'
    PARSE_TASK = 'parse_tasks'
    SAVE_PARSED_DATA = 'save_parsed_text_content'
    PROCESS_LINKS = 'process_links'

    # Queues For 'Link Processing Task'
    SAVE_PROCESSED_LINKS = 'save_processed_links'
    CACHE_PROCESSED_LINKS = 'cache_processed_links'


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
    LISTEN = QueueNames.CRAWL_TASK.value,
    SAVE_PAGE_DATA = QueueNames.SAVE_PAGE_DATA.value,
    PARSE = QueueNames.PARSE_TASK.value


# Parser queue channels
class ParserQueueChannels(EnumCommonMethods, str, Enum):
    LISTEN = QueueNames.PARSE_TASK.value,
    SAVE_PARSED_DATA = QueueNames.SAVE_PARSED_DATA.value,
    PROCESS_LINKS = QueueNames.PROCESS_LINKS.value


# DB Writer queue channels
class DbServiceQueueChannels(EnumCommonMethods, str, Enum):
    SAVE_CRAWL_DATA = QueueNames.SAVE_PAGE_DATA.value,
    SAVE_PARSED_DATA = QueueNames.SAVE_PARSED_DATA.value,
    SAVE_PROCESSED_LINKS = QueueNames.SAVE_PROCESSED_LINKS.value
    CACHE_PROCESSED_LINKS = QueueNames.CACHE_PROCESSED_LINKS.value


# Scheduler queue channels
class SchedulerQueueChannels(EnumCommonMethods, str, Enum):
    ADD_TO_QUEUE = QueueNames.CRAWL_TASK.value,
    PROCESS_LINKS = QueueNames.PROCESS_LINKS.value,
    SAVE_PROCESSED_LINKS = QueueNames.SAVE_PROCESSED_LINKS.value
    CACHE_PROCESSED_LINKS = QueueNames.CACHE_PROCESSED_LINKS.value

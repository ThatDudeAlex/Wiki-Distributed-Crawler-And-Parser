
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
from shared.rabbitmq.enums.crawl_status import CrawlStatus


@dataclass
class QueueMsgSchemaInterface(ABC):
    """Base class for all rabbitmq message schemas"""

    def is_valid_url(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        result = urlparse(url)
        return all([result.scheme, result.netloc])

    @abstractmethod
    def validate(self) -> None:
        pass


class ValidationError(Exception):
    """Raised when a message schema fails validation"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        full_msg = f"{field}: {message}" if field else message
        super().__init__(full_msg)


@dataclass
class PageMetadata:
    status: CrawlStatus
    fetched_at: datetime
    url: str
    http_status_code: Optional[int] = None
    url_hash: Optional[str] = None
    html_content_hash: Optional[str] = None
    compressed_filepath: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ParsedContent:
    source_page_url: str
    title: str
    parsed_at: datetime
    summary: Optional[str] = None
    text_content: Optional[str] = None
    text_content_hash: Optional[str] = None
    categories: Optional[List[str]] = None


@dataclass
class DiscoveredLink:
    url: str
    depth: int
    anchor_text: str
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None
    is_internal: bool = False


@dataclass
class ProcessDiscoveredLinks:
    source_page_url: str
    discovered_at: datetime
    links: List[DiscoveredLink]

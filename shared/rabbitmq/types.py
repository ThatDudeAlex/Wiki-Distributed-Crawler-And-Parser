
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
from shared.rabbitmq.enums.crawl_status import CrawlStatus


@dataclass
class QueueMsgSchemaInterface(ABC):
    """Base class for all rabbitmq message schemas"""

    def to_dict(self) -> dict:
        return asdict(self)

    def is_valid_url(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        result = urlparse(url)
        return all([result.scheme, result.netloc])

    @abstractmethod
    def validate_publish(self) -> None:
        pass

    @abstractmethod
    def validate_consume(self) -> None:
        pass


class ValidationError(Exception):
    """Raised when a message schema fails validation"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        full_msg = f"{field}: {message}" if field else message
        super().__init__(full_msg)


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

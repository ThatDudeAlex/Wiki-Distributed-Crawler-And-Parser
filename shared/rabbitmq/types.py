
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from shared.rabbitmq.enums.crawl_status import CrawlStatus


# TODO: Pydantic - For each pydantic message model, create a @dataclass for it.
# That way i can easily convert into it after doing validation, and not have to deal
# with the pydantic errors that can occurr when used in internal logic

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

from dataclasses import dataclass
from pathlib import Path
from pydantic import BaseModel, HttpUrl, FilePath
from typing import List, Optional
from database.db_models.models import CrawlStatus


class SavePageTaskSchema(BaseModel):
    url: HttpUrl
    url_hash: Optional[str]
    crawl_time: str
    crawl_status: CrawlStatus
    status_code: Optional[int]
    compressed_path: Optional[FilePath]


class SaveParsedContentSchema(BaseModel):
    page_url: HttpUrl
    title: str
    summary: str
    content: str
    parse_time: str
    categories: Optional[list[str]]


@dataclass
class SavePageTask:
    url: str
    url_hash: Optional[str] = None
    crawl_time: str
    crawl_status: CrawlStatus
    status_code: Optional[int] = None
    compressed_path: Optional[Path] = None


@dataclass
class SaveParsedContent:
    page_url: str
    title: str
    summary: str
    content: str
    parse_time: str
    categories: Optional[List[str]] = None

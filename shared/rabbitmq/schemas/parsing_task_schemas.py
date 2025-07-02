from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, FilePath, HttpUrl


# === Parsing Task (Crawler → Parser) ===

class ParsingTask(BaseModel):
    url: HttpUrl
    depth: int
    compressed_filepath: FilePath


# === Save Parsed Content (Parser → DB Writer) ===

class ParsedContentsMessage(BaseModel):
    # Requires 'message.model_dump_json()' before publishing to queue
    source_page_url: HttpUrl
    title: str
    summary:           str | None = None
    text_content:      str | None = None
    text_content_hash: str | None = None
    categories:  List[str] | None = None
    parsed_at: datetime


# === Process Discovered Links (Parser → Scheduler) ===

class DiscoveredLink(BaseModel):
    url: HttpUrl
    depth: int
    anchor_text: str
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None
    is_internal: bool = False


class ProcessDiscoveredLinks(BaseModel):
    source_page_url: HttpUrl
    discovered_at: datetime
    links: List[DiscoveredLink]

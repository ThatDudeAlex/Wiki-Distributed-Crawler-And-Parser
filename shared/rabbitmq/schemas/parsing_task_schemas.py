from datetime import datetime
from typing import List
from pydantic import BaseModel, FilePath, HttpUrl


# === Parsing Task (Crawler → Parser) ===

class ParsingTask(BaseModel):
    url: HttpUrl
    compressed_path: FilePath


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

class ProcessDiscoveredLinks(BaseModel):
    source_page_url: HttpUrl
    discovered_at: datetime
    links: list[HttpUrl]

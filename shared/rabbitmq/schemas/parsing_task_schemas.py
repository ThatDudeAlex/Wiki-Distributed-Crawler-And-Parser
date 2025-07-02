from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, FilePath, HttpUrl
from shared.rabbitmq.types import ParsedContent


# === Parsing Task (Crawler → Parser) ===

# TODO: Pydantic - Create a dataclass to convert this class into
class ParsingTask(BaseModel):
    url: HttpUrl
    depth: int
    compressed_filepath: FilePath


# === Save Parsed Content (Parser → DB Writer) ===

# TODO: Pydantic - Create a BaseClass that includes to_dataclass()
class ParsedContentsMessage(BaseModel):
    # Requires 'message.model_dump_json()' before publishing to queue
    source_page_url: HttpUrl
    title: str
    summary:           Optional[str] = None
    text_content:      Optional[str] = None
    text_content_hash: Optional[str] = None
    parsed_at: datetime
    categories:  Optional[List[str]] = None

    def to_dataclass(self) -> ParsedContent:
        return ParsedContent(
            source_page_url=str(self.source_page_url),
            title=self.title,
            parsed_at=self.parsed_at,
            summary=self.summary,
            text_content=self.text_content,
            text_content_hash=self.text_content_hash,
            categories=self.categories,
        )


# === Process Discovered Links (Parser → Scheduler) ===

# TODO: Pydantic - Create a dataclass to convert this class into
class DiscoveredLink(BaseModel):
    url: HttpUrl
    depth: int
    anchor_text: str
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None
    is_internal: bool = False


# TODO: Pydantic - Create a dataclass to convert this class into
class ProcessDiscoveredLinks(BaseModel):
    source_page_url: HttpUrl
    discovered_at: datetime
    links: List[DiscoveredLink]

from dataclasses import dataclass, field
from pydantic import BaseModel
from typing import List, Optional

from shared.rabbitmq.schemas.parsing_task_schemas import DiscoveredLink, ParsedContentsMessage


class LinkDataSchema(BaseModel):
    to_url: str
    anchor_text: str
    title: Optional[str]
    rel: Optional[List[str]]
    id_attr: Optional[str]
    classes: Optional[List[str]]
    is_internal: bool
    link_type: str


@dataclass
class LinkData:
    url: str
    depth: int
    anchor_text: str
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None
    is_internal: bool = False

    def to_discovered_link(self) -> DiscoveredLink:
        return DiscoveredLink(
            url=self.url,
            depth=self.depth,
            anchor_text=self.anchor_text,
            title_attribute=self.title_attribute,
            rel_attribute=self.rel_attribute,
            id_attribute=self.id_attribute,
            link_type=self.link_type,
            is_internal=self.is_internal
        )


@dataclass
class PageContent:
    source_page_url: str
    title: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    text_content: Optional[str] = None
    text_content_hash: Optional[str] = None
    parsed_at: Optional[str] = None

    def to_parsed_contents_message(self) -> ParsedContentsMessage:
        return ParsedContentsMessage(
            source_page_url=self.source_page_url,
            title=self.title,
            # If empty list make it None
            categories=self.categories if self.categories else None,
            summary=self.summary,
            text_content=self.text_content,
            text_content_hash=self.text_content_hash,
            parsed_at=self.parsed_at
        )

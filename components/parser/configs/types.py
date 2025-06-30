from dataclasses import dataclass, field
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class LinkData(BaseModel):
    original_href: str
    to_url: str
    anchor_text: str
    title: Optional[str]
    rel: Optional[List[str]]
    id_attr: Optional[str]
    classes: Optional[List[str]]
    is_internal: bool
    link_type: str


class PageContentSchema(BaseModel):
    page_url: HttpUrl
    title: Optional[str]
    categories: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str]
    text_content: Optional[str]
    text_content_hash: Optional[str]
    parsed_at: Optional[str]


@dataclass
class LinkData:
    original_href: str
    to_url: str
    anchor_text: str
    title: Optional[str] = None
    rel: Optional[List[str]] = None
    id_attr: Optional[str] = None
    classes: Optional[List[str]] = None
    is_internal: bool = False
    link_type: str = ""


@dataclass
class PageContent:
    page_url: str
    title: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    text_content: Optional[str] = None
    text_content_hash: Optional[str] = None
    parsed_at: Optional[str] = None

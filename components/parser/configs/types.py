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


class PageContent(BaseModel):
    url: HttpUrl
    title: Optional[str]
    categories: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str]
    text_content: Optional[str]
    text_content_hash: Optional[str]
    parsed_at: Optional[str]

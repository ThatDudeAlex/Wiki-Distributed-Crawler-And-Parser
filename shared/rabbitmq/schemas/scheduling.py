from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse

class LinkData(BaseModel):
    source_page_url: str
    url: str
    depth: int
    discovered_at: str
    is_internal: bool = False
    anchor_text: Optional[str] = None
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None

    @field_validator("url")
    @classmethod
    def must_be_valid_url(cls, url: str) -> str:
        result = urlparse(url)
        if not (result.scheme and result.netloc):
            raise ValueError("Invalid URL format")
        return url
    
    @field_validator("depth")
    @classmethod
    def validate_depth(cls, depth: int) -> int:
        if depth < 0:
            raise ValueError("Depth must be a non-negative integer")
        return depth
    
    @field_validator("discovered_at")
    @classmethod
    def validate_iso_datetime(cls, discovered_at: str) -> str:
        try:
            datetime.fromisoformat(discovered_at)
        except ValueError:
            raise ValueError("discovered_at must be a valid ISO 8601 datetime string")
        return discovered_at
    
class ProcessDiscoveredLinks(BaseModel):
    links: List[LinkData]
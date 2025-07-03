from dataclasses import dataclass
from pydantic import BaseModel
from typing import List, Optional

from shared.rabbitmq.schemas.parsing_task_schemas import DiscoveredLinkPydanticModel


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

    def to_discovered_link(self) -> DiscoveredLinkPydanticModel:
        return DiscoveredLinkPydanticModel(
            url=self.url,
            depth=self.depth,
            anchor_text=self.anchor_text,
            title_attribute=self.title_attribute,
            rel_attribute=self.rel_attribute,
            id_attribute=self.id_attribute,
            link_type=self.link_type,
            is_internal=self.is_internal
        )

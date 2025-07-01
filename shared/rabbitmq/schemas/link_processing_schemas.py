from pydantic import BaseModel, HttpUrl
from datetime import datetime


# === Save Link Record (Scheduler → DB Writer) ===

class LinkRecord(BaseModel):
    source_page_url: HttpUrl | None  # only None when seeded or imported
    url: HttpUrl
    depth: int
    is_internal: bool = False
    anchor_text: str | None

    id_attribute:    str | None
    rel_attribute:   str | None
    title_attribute: str | None
    link_type: str | None
    discovered_at: datetime


class SaveLinksPayload(BaseModel):
    links: list[LinkRecord]

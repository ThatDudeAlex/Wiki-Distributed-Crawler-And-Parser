from pydantic import BaseModel, HttpUrl
from datetime import datetime


# === Save Link Record (Scheduler → DB Writer) ===

class LinkRecord(BaseModel):
    url: HttpUrl
    source_url: HttpUrl | None
    discovered_at: datetime
    depth: int


class SaveLinksPayload(BaseModel):
    links: list[LinkRecord]

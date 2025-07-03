from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, FilePath, HttpUrl
from shared.rabbitmq.schemas.crawling_task_schemas import ValidationError
from shared.rabbitmq.types import ParsedContent, ProcessDiscoveredLinks, QueueMsgSchemaInterface


# === Parsing Task (Crawler → Parser) ===

@dataclass
class ParsingTask(QueueMsgSchemaInterface):
    url: str
    depth: int
    compressed_filepath: str

    def _validate(self) -> None:
        # Validate URL
        if not self.url or not self.is_valid_url(self.url):
            raise ValidationError("Invalid or missing URL", field="url")

        # Validate depth
        if not isinstance(self.depth, int) or self.depth < 0:
            raise ValidationError(
                "Depth must be a non-negative integer", field="depth")

        # Validate compressed_filepath
        if not isinstance(self.compressed_filepath, str) or not self.compressed_filepath.strip():
            raise ValidationError(
                "compressed_filepath must be a non-empty string", field="compressed_filepath")

    def validate_publish(self) -> None:
        self._validate()

    def validate_consume(self) -> None:
        self._validate()


# === Save Parsed Content (Parser → DB Writer) ===

# @dataclass
# class ParsedContent:
#     source_page_url: str
#     title: str
#     parsed_at: datetime
#     summary: Optional[str] = None
#     text_content: Optional[str] = None
#     text_content_hash: Optional[str] = None
#     categories: Optional[List[str]] = None

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
class DiscoveredLinkPydanticModel(BaseModel):
    url: HttpUrl
    depth: int
    anchor_text: str
    title_attribute: Optional[str] = None
    rel_attribute: Optional[str] = None
    id_attribute: Optional[str] = None
    link_type: Optional[str] = None
    is_internal: bool = False


# TODO: Pydantic - Create a dataclass to convert this class into
# TODO: This class and SaveLinksPayload can be merged
class ProcessDiscoveredLinksMsg(BaseModel):
    source_page_url: HttpUrl
    discovered_at: datetime
    links: List[DiscoveredLinkPydanticModel]

    def to_dataclass(self) -> ProcessDiscoveredLinks:
        discovered_links_dc = [
            DiscoveredLinkPydanticModel(
                url=str(link.url),  # Convert HttpUrl to string
                depth=link.depth,
                anchor_text=link.anchor_text,
                title_attribute=link.title_attribute,
                rel_attribute=link.rel_attribute,
                id_attribute=link.id_attribute,
                link_type=link.link_type,
                is_internal=link.is_internal,
            )
            for link in self.links
        ]
        return ProcessDiscoveredLinks(
            # Convert HttpUrl to string
            source_page_url=str(self.source_page_url),
            discovered_at=self.discovered_at,
            links=discovered_links_dc,
        )

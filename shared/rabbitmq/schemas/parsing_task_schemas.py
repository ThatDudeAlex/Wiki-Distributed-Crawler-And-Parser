from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from shared.rabbitmq.schemas.crawling_task_schemas import ValidationError
from shared.rabbitmq.types import ProcessDiscoveredLinks, QueueMsgSchemaInterface


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

@dataclass
class ParsedContent(QueueMsgSchemaInterface):
    source_page_url: str
    title: str
    parsed_at: datetime
    summary: Optional[str] = None
    text_content: Optional[str] = None
    text_content_hash: Optional[str] = None
    categories: Optional[List[str]] = None

    def _validate(self) -> None:
        # Validate source_page_url
        if not self.source_page_url or not self.is_valid_url(self.source_page_url):
            raise ValidationError(
                "Invalid or missing source_page_url", field="source_page_url")

        # Validate title
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValidationError(
                "Title must be a non-empty string", field="title")

        # Validate text_content_hash if present
        if self.text_content_hash is not None:
            if not isinstance(self.text_content_hash, str) or not self.text_content_hash.strip():
                raise ValidationError(
                    "text_content_hash must be a non-empty string if provided", field="text_content_hash")

        # Validate categories if present
        if self.categories is not None:
            if not isinstance(self.categories, list):
                raise ValidationError(
                    "categories must be a list of strings", field="categories")
            for i, category in enumerate(self.categories):
                if not isinstance(category, str) or not category.strip():
                    raise ValidationError(
                        f"Category at index {i} must be a non-empty string", field="categories")

    def validate_publish(self) -> None:
        self._validate()
        # parsed_at must be a datetime obj — convert to ISO 8601 string
        if not isinstance(self.parsed_at, datetime):
            raise ValidationError(
                "parsed_at must be a datetime object before publishing", field="parsed_at")
        # Convert field to ISO string for JSON serialization
        self.parsed_at = self.parsed_at.isoformat()

    def validate_consume(self) -> None:
        # parsed_at must be a string — convert to datetime
        if not isinstance(self.parsed_at, str):
            raise ValidationError(
                "parsed_at must be a ISO 8601 string when consuming", field="parsed_at")

        try:
            self.parsed_at = datetime.fromisoformat(self.parsed_at)
        except ValueError:
            raise ValidationError(
                "parsed_at must be a valid ISO 8601 datetime string", field="parsed_at")
        self._validate()

# === Process Discovered Links (Parser → Scheduler) ===


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

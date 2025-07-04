from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from shared.rabbitmq.schemas.crawling_task_schemas import ValidationError
from shared.rabbitmq.types import QueueMsgSchemaInterface


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
        if not isinstance(self.parsed_at, datetime):
            raise ValidationError(
                "parsed_at must be a datetime object before publishing", field="parsed_at")
        # Convert to ISO string for JSON serialization
        self.parsed_at = self.parsed_at.isoformat()

    def validate_consume(self) -> None:
        if not isinstance(self.parsed_at, str):
            raise ValidationError(
                "parsed_at must be a ISO 8601 string when consuming", field="parsed_at")

        try:
            # convert to datetime
            self.parsed_at = datetime.fromisoformat(self.parsed_at)
        except ValueError:
            raise ValidationError(
                "parsed_at must be a valid ISO 8601 datetime string", field="parsed_at")
        self._validate()


# === Process Discovered Links (Parser → Scheduler) ===

@dataclass
class LinkData(QueueMsgSchemaInterface):
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

    def _validate(self) -> None:
        # Validate source_page_url
        if not self.source_page_url or not self.is_valid_url(self.source_page_url):
            raise ValidationError(
                "Invalid or missing source_page_url", field="source_page_url")

        # Validate url
        if not self.url or not self.is_valid_url(self.url):
            raise ValidationError("Invalid or missing url", field="url")

        # Validate depth
        if not isinstance(self.depth, int) or self.depth < 0:
            raise ValidationError(
                "depth must be a non-negative integer", field="depth")

        # Validate discovered_at
        if not isinstance(self.discovered_at, str):
            raise ValidationError(
                "discovered_at must be a string", field="discovered_at")

        try:
            datetime.fromisoformat(self.discovered_at)
        except ValueError:
            raise ValidationError(
                "discovered_at must be a valid ISO 8601 timestamp", field="discovered_at")

        # Validate is_internal
        if not isinstance(self.is_internal, bool):
            raise ValidationError(
                "is_internal must be a boolean", field="is_internal")

        # Validate optional string fields
        for field_name in [
            "title_attribute", "rel_attribute", "id_attribute", "link_type", "anchor_text"
        ]:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValidationError(
                    f"{field_name} must be a string if provided", field=field_name)

    def validate_publish(self) -> None:
        self._validate()

    def validate_consume(self) -> None:
        self._validate()


@dataclass
class ProcessDiscoveredLinks(QueueMsgSchemaInterface):
    links: List[LinkData]

    def _validate(self) -> None:
        if not isinstance(self.links, list) or not self.links:
            raise ValidationError(
                "links must be a non-empty list", field="links")

    def validate_publish(self) -> None:
        self._validate()

        # Validate each LinkData using publish context
        for i, link in enumerate(self.links):
            if not isinstance(link, LinkData):
                raise ValidationError(
                    f"links[{i}] must be a LinkData instance", field=f"links[{i}]")
            try:
                link.validate_publish()
            except ValidationError as e:
                raise ValidationError(str(e), field=f"links[{i}]")

    def validate_consume(self) -> None:
        # Convert link dicts to LinkData instances
        for i, link in enumerate(self.links):
            if isinstance(link, dict):
                try:
                    self.links[i] = LinkData(**link)
                except Exception as e:
                    raise ValidationError(
                        f"Failed to parse link[{i}]: {e}", field=f"links[{i}]")

            try:
                self.links[i].validate_consume()
            except ValidationError as e:
                raise ValidationError(str(e), field=f"links[{i}]")

        self._validate()
